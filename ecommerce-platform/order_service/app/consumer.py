"""
Runs as a separate process from the FastAPI app (app.main:app), since a
blocking Kafka consume loop cannot share a process with a request-serving
HTTP server. In docker-compose this is a second container built from the
same image, with its CMD overridden to run this module instead of uvicorn.
"""
import logging

from app.api.dependencies import get_order_service
from app.infrastructure.messaging.event_consumer import KafkaPaymentEventConsumer

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    consumer = KafkaPaymentEventConsumer(order_service=get_order_service())
    consumer.start()
