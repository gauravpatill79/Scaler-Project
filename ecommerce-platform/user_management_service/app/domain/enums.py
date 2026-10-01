from enum import Enum


class UserStatus(str, Enum):
    """Lifecycle states of a user account."""
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class AuthProviderType(str, Enum):
    """Supported authentication providers (maps to Strategy pattern)."""
    EMAIL_PASSWORD = "EMAIL_PASSWORD"
    GOOGLE = "GOOGLE"
    FACEBOOK = "FACEBOOK"
    APPLE = "APPLE"


class UserEventType(str, Enum):
    """Kafka event topics/types this service publishes."""
    USER_REGISTERED = "user.registered"
    USER_PROFILE_UPDATED = "user.profile_updated"
    USER_LOGGED_IN = "user.logged_in"
    PASSWORD_RESET_REQUESTED = "user.password_reset_requested"
    PASSWORD_RESET_COMPLETED = "user.password_reset_completed"
