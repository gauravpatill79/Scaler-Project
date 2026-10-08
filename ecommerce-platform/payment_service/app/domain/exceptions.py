class DomainError(Exception):
    http_status: int = 400


class PaymentNotFoundError(DomainError):
    http_status = 404

    def __init__(self, identifier: str):
        super().__init__(f"Payment '{identifier}' was not found")


class InvalidPaymentAmountError(DomainError):
    http_status = 422

    def __init__(self, amount):
        super().__init__(f"Payment amount must be greater than zero, got {amount}")


class UnsupportedPaymentMethodError(DomainError):
    http_status = 422

    def __init__(self, method: str):
        super().__init__(f"Payment method '{method}' is not supported")


class PaymentGatewayError(DomainError):
    http_status = 502

    def __init__(self, method: str, reason: str):
        super().__init__(f"Gateway error processing {method} payment: {reason}")


class RefundNotAllowedError(DomainError):
    http_status = 409

    def __init__(self, payment_id: str, status: str):
        super().__init__(f"Payment '{payment_id}' cannot be refunded from status '{status}'")


class ReceiptNotAvailableError(DomainError):
    http_status = 409

    def __init__(self, payment_id: str, status: str):
        super().__init__(f"No receipt available for payment '{payment_id}' — status is '{status}'")
