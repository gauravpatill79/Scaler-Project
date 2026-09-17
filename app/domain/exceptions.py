class DomainError(Exception):
    """Base class for all domain-level errors. Maps to a 4xx HTTP response."""
    http_status: int = 400


class UserAlreadyExistsError(DomainError):
    http_status = 409

    def __init__(self, email: str):
        super().__init__(f"A user with email '{email}' already exists")


class UserNotFoundError(DomainError):
    http_status = 404

    def __init__(self, identifier: str):
        super().__init__(f"User '{identifier}' was not found")


class InvalidCredentialsError(DomainError):
    http_status = 401

    def __init__(self):
        super().__init__("Invalid email or password")


class AccountNotActiveError(DomainError):
    http_status = 403

    def __init__(self, status: str):
        super().__init__(f"Account is not active (current status: {status})")


class InvalidOrExpiredTokenError(DomainError):
    http_status = 400

    def __init__(self, token_purpose: str = "token"):
        super().__init__(f"The provided {token_purpose} is invalid or has expired")


class WeakPasswordError(DomainError):
    http_status = 422

    def __init__(self, reason: str):
        super().__init__(f"Password does not meet policy: {reason}")
