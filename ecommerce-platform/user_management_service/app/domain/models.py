"""
Domain entities for the User Management Service.

These classes are plain Python objects (no ORM/framework coupling) so business
rules live in one place and stay testable in isolation. This is the
Domain Model pattern combined with an Anemic-avoidance principle: entities
own the behaviour that belongs to them (e.g. User.deactivate()), instead of
services mutating public fields directly.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.domain.enums import AuthProviderType, UserStatus
from app.domain.exceptions import AccountNotActiveError


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class UserProfile:
    user_id: str
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    date_of_birth: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None

    def full_name(self) -> str:
        return " ".join(p for p in [self.first_name, self.last_name] if p) or "Unnamed user"

    def update(self, **fields) -> None:
        """Only assign known, non-None fields — keeps partial updates safe."""
        for key, value in fields.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)


@dataclass
class SocialAccount:
    user_id: str
    provider: AuthProviderType
    provider_user_id: str
    id: str = field(default_factory=_new_id)
    linked_at: datetime = field(default_factory=_utcnow)


@dataclass
class PasswordResetToken:
    user_id: str
    token_hash: str
    expires_at: datetime
    id: str = field(default_factory=_new_id)
    used: bool = False
    created_at: datetime = field(default_factory=_utcnow)

    def is_valid(self) -> bool:
        return (not self.used) and _utcnow() < self.expires_at

    def mark_used(self) -> None:
        self.used = True


@dataclass
class User:
    email: str
    id: str = field(default_factory=_new_id)
    password_hash: str | None = None
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    failed_login_attempts: int = 0
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    # ---- behaviour lives on the entity, not scattered across services ----

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE
        self.updated_at = _utcnow()

    def deactivate(self) -> None:
        self.status = UserStatus.DEACTIVATED
        self.updated_at = _utcnow()

    def suspend(self) -> None:
        self.status = UserStatus.SUSPENDED
        self.updated_at = _utcnow()

    def ensure_active(self) -> None:
        if self.status != UserStatus.ACTIVE:
            raise AccountNotActiveError(self.status.value)

    def record_successful_login(self) -> None:
        self.failed_login_attempts = 0
        self.last_login_at = _utcnow()
        self.updated_at = _utcnow()

    def record_failed_login(self) -> None:
        self.failed_login_attempts += 1
        self.updated_at = _utcnow()
        if self.failed_login_attempts >= 5:
            self.suspend()

    def set_password_hash(self, new_hash: str) -> None:
        self.password_hash = new_hash
        self.updated_at = _utcnow()

    @staticmethod
    def new_reset_token(user_id: str, token_hash: str, ttl_minutes: int = 30) -> PasswordResetToken:
        return PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=_utcnow() + timedelta(minutes=ttl_minutes),
        )
