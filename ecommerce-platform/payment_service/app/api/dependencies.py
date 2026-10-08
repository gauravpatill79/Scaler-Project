from __future__ import annotations

from functools import lru_cache

from app.infrastructure.gateways.payment_gateway import PaymentGatewayFactory
from app.infrastructure.messaging.event_publisher import EventPublisher, KafkaEventPublisher
from app.repository.interfaces import PaymentRepository
from app.repository.mysql_repository import MySQLPaymentRepository
from app.services.payment_service import PaymentService


@lru_cache
def get_payment_repository() -> PaymentRepository:
    return MySQLPaymentRepository()


@lru_cache
def get_gateway_factory() -> PaymentGatewayFactory:
    return PaymentGatewayFactory()


@lru_cache
def get_event_publisher() -> EventPublisher:
    return KafkaEventPublisher()


def get_payment_service() -> PaymentService:
    return PaymentService(get_payment_repository(), get_gateway_factory(), get_event_publisher())
