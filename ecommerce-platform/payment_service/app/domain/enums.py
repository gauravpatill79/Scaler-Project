from enum import Enum


class PaymentMethod(str, Enum):
    CARD = "CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"
    UPI = "UPI"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentEventType(str, Enum):
    """Kafka event topics this service publishes. Order Management Service
    consumes these to advance an order's state machine (see that service's
    KafkaPaymentEventConsumer, built before this service existed)."""
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
