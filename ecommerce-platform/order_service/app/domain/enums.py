from enum import Enum


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class OrderEventType(str, Enum):
    """Kafka event topics this service publishes. Payment Service consumes
    ORDER_CREATED to begin processing payment, per the HLD's checkout flow."""
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_PROCESSING = "order.processing"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_PAYMENT_FAILED = "order.payment_failed"
