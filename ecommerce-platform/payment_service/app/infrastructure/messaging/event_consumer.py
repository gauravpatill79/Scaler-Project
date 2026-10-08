"""
The second Kafka consumer in the system, mirroring the pattern Order
Management Service established with its own payment-event consumer.
Listens for `order.created` (begins payment processing, per the HLD's
checkout flow) and `order.cancelled` (triggers a refund if the order had
already been paid).

Order Management Service publishes these events with `order_id` as the
top-level key and event-specific fields inside `payload` — this consumer
reads that exact shape, since it is the contract Order Service's own
README already documents for this service to honor.
"""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from decimal import Decimal

logger = logging.getLogger(__name__)

ORDER_CREATED_TOPIC = "order.created"
ORDER_CANCELLED_TOPIC = "order.cancelled"


class OrderEventConsumer(ABC):
    @abstractmethod
    def start(self) -> None: ...


class KafkaOrderEventConsumer(OrderEventConsumer):
    def __init__(self, payment_service, bootstrap_servers: str | None = None, group_id: str = "payment-service-order-consumer"):
        self._payment_service = payment_service
        self._bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._group_id = group_id

    def start(self) -> None:
        from kafka import KafkaConsumer

        consumer = KafkaConsumer(
            ORDER_CREATED_TOPIC,
            ORDER_CANCELLED_TOPIC,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        logger.info("Order event consumer started, listening on %s and %s", ORDER_CREATED_TOPIC, ORDER_CANCELLED_TOPIC)

        for message in consumer:
            self._handle_message(message.topic, message.value)

    def _handle_message(self, topic: str, event: dict) -> None:
        order_id = event.get("order_id")
        if not order_id:
            logger.error("Received %s event with no order_id: %s", topic, event)
            return

        try:
            if topic == ORDER_CREATED_TOPIC:
                payload = event.get("payload", {})
                self._payment_service.process_payment(
                    order_id=order_id,
                    user_id=payload["user_id"],
                    amount=Decimal(payload["total_amount"]),
                    currency=payload.get("currency", "INR"),
                    method=payload["payment_method"],
                )
            elif topic == ORDER_CANCELLED_TOPIC:
                self._payment_service.refund_payment(order_id)
        except Exception:
            logger.exception("Failed to process %s event for order %s", topic, order_id)
