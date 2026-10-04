"""
This is the system's first real Kafka consumer. Every service built so far
only publishes events; Order Service is the first to react to another
service's events, closing the HLD's checkout flow (Part 3): Payment Service
consumes `order.created`, processes payment, and publishes `payment.completed`
or `payment.failed` — this consumer reacts to those and drives the order's
state machine forward.

Payment Service does not exist yet. The topic names and payload shape below
are the contract this consumer expects; Payment Service must publish to
these topics with an `order_id` field in its payload when it is built.
"""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

PAYMENT_COMPLETED_TOPIC = "payment.completed"
PAYMENT_FAILED_TOPIC = "payment.failed"


class PaymentEventConsumer(ABC):
    @abstractmethod
    def start(self) -> None: ...


class KafkaPaymentEventConsumer(PaymentEventConsumer):
    def __init__(self, order_service, bootstrap_servers: str | None = None, group_id: str = "order-service-payment-consumer"):
        self._order_service = order_service
        self._bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._group_id = group_id

    def start(self) -> None:
        from kafka import KafkaConsumer

        consumer = KafkaConsumer(
            PAYMENT_COMPLETED_TOPIC,
            PAYMENT_FAILED_TOPIC,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        logger.info("Payment event consumer started, listening on %s and %s", PAYMENT_COMPLETED_TOPIC, PAYMENT_FAILED_TOPIC)

        for message in consumer:
            self._handle_message(message.topic, message.value)

    def _handle_message(self, topic: str, event: dict) -> None:
        order_id = event.get("payload", {}).get("order_id")
        if not order_id:
            logger.error("Received %s event with no order_id in payload: %s", topic, event)
            return

        try:
            if topic == PAYMENT_COMPLETED_TOPIC:
                self._order_service.handle_payment_confirmed(order_id)
            elif topic == PAYMENT_FAILED_TOPIC:
                self._order_service.handle_payment_failed(order_id)
        except Exception:
            logger.exception("Failed to process %s event for order %s", topic, order_id)
