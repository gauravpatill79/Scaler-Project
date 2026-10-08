"""
Runs as a separate process from the FastAPI app, same rationale as Order
Management Service's consumer.py.
"""
import logging

from app.api.dependencies import get_payment_service
from app.infrastructure.messaging.event_consumer import KafkaOrderEventConsumer

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    consumer = KafkaOrderEventConsumer(payment_service=get_payment_service())
    consumer.start()
