"""
process_payment is idempotent on order_id: Kafka's at-least-once delivery
means `order.created` could be redelivered, and this must not double-charge.
A payment row is written as PENDING before the gateway is called, so a
crash between the gateway call and the status update leaves a durable,
inspectable PENDING record rather than silently losing the attempt. MySQL
is the only write that can fail a request; the Kafka publish after a
status change is best-effort and logged, matching every other service.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from app.domain.enums import PaymentEventType, PaymentMethod, PaymentStatus
from app.domain.exceptions import (
    InvalidPaymentAmountError,
    PaymentNotFoundError,
    ReceiptNotAvailableError,
    UnsupportedPaymentMethodError,
)
from app.domain.models import Payment
from app.infrastructure.gateways.payment_gateway import PaymentGatewayFactory
from app.infrastructure.messaging.event_publisher import EventPublisher, PaymentEvent
from app.repository.interfaces import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, repo: PaymentRepository, gateway_factory: PaymentGatewayFactory, publisher: EventPublisher):
        self._repo = repo
        self._gateways = gateway_factory
        self._publisher = publisher

    def _safe_publish(self, topic: str, event: PaymentEvent) -> None:
        try:
            self._publisher.publish(topic, event)
        except Exception:
            logger.exception("Failed to publish %s event for payment %s", topic, event.payment_id)

    def process_payment(
        self, order_id: str, user_id: str, amount: Decimal, currency: str, method: str
    ) -> Payment:
        existing = self._repo.find_by_order_id(order_id)
        if existing is not None:
            logger.info("Payment already processed for order %s, skipping re-charge", order_id)
            return existing

        if amount <= 0:
            raise InvalidPaymentAmountError(amount)
        try:
            method_enum = PaymentMethod(method)
        except ValueError as exc:
            raise UnsupportedPaymentMethodError(method) from exc

        payment = Payment(order_id=order_id, user_id=user_id, amount=amount, currency=currency, method=method_enum)
        self._repo.save(payment)  # durable PENDING record before the gateway is touched

        gateway = self._gateways.get_strategy(method_enum)
        previous_status = payment.status
        result = gateway.charge(amount, currency, {})

        if result.success:
            payment.mark_success(result.gateway_reference)
            self._repo.save(payment, previous_status=previous_status)
            self._safe_publish(
                PaymentEventType.PAYMENT_COMPLETED.value,
                PaymentEvent(
                    PaymentEventType.PAYMENT_COMPLETED,
                    payment.id,
                    {"order_id": order_id, "amount": str(amount), "gateway_reference": result.gateway_reference},
                ),
            )
        else:
            payment.mark_failed(result.failure_reason or "Gateway declined the payment")
            self._repo.save(payment, previous_status=previous_status)
            self._safe_publish(
                PaymentEventType.PAYMENT_FAILED.value,
                PaymentEvent(
                    PaymentEventType.PAYMENT_FAILED,
                    payment.id,
                    {"order_id": order_id, "reason": payment.failure_reason},
                ),
            )
        return payment

    def get_payment(self, payment_id: str) -> Payment:
        payment = self._repo.find_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(payment_id)
        return payment

    def get_payment_for_order(self, order_id: str) -> Payment:
        payment = self._repo.find_by_order_id(order_id)
        if payment is None:
            raise PaymentNotFoundError(order_id)
        return payment

    def get_receipt(self, payment_id: str) -> dict:
        payment = self.get_payment(payment_id)
        if payment.status != PaymentStatus.SUCCESS:
            raise ReceiptNotAvailableError(payment_id, payment.status.value)
        return {
            "receipt_number": payment.receipt_number,
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "method": payment.method.value,
            "paid_at": payment.updated_at,
        }

    def refund_payment(self, order_id: str) -> Payment:
        payment = self._repo.find_by_order_id(order_id)
        if payment is None:
            raise PaymentNotFoundError(order_id)

        if payment.status == PaymentStatus.REFUNDED:
            logger.info("Payment for order %s already refunded, skipping", order_id)
            return payment

        previous_status = payment.status
        payment.mark_refunded()
        self._repo.save(payment, previous_status=previous_status)
        self._safe_publish(
            PaymentEventType.PAYMENT_REFUNDED.value,
            PaymentEvent(PaymentEventType.PAYMENT_REFUNDED, payment.id, {"order_id": order_id}),
        )
        return payment
