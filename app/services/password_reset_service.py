from __future__ import annotations

import hashlib
import secrets

from app.domain.enums import UserEventType
from app.domain.exceptions import InvalidOrExpiredTokenError, WeakPasswordError
from app.infrastructure.messaging.event_publisher import EventPublisher, UserEvent
from app.infrastructure.security.password_hasher import PasswordHasher
from app.repository.interfaces import PasswordResetRepository, UserRepository
from app.services.user_service import MIN_PASSWORD_LENGTH


def _hash_token(raw_token: str) -> str:
    # Reset tokens are single-use and short-lived, so a fast SHA-256 digest
    # (rather than bcrypt) is sufficient and keeps lookups cheap.
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class PasswordResetService:
    def __init__(
        self,
        user_repo: UserRepository,
        reset_repo: PasswordResetRepository,
        hasher: PasswordHasher,
        publisher: EventPublisher,
    ):
        self._user_repo = user_repo
        self._reset_repo = reset_repo
        self._hasher = hasher
        self._publisher = publisher

    def request_reset(self, email: str) -> str | None:
        """Returns the raw token to embed in the emailed reset link.
        Returns None silently if the email is unknown — never reveal
        whether an email is registered (prevents user enumeration).
        """
        user = self._user_repo.find_by_email(email)
        if user is None:
            return None

        raw_token = secrets.token_urlsafe(32)
        reset_token = user.new_reset_token(user.id, _hash_token(raw_token))
        self._reset_repo.save(reset_token)

        self._publisher.publish(
            UserEventType.PASSWORD_RESET_REQUESTED.value,
            UserEvent(
                event_type=UserEventType.PASSWORD_RESET_REQUESTED,
                user_id=user.id,
                payload={"email": user.email},  # Notification Service sends the actual email
            ),
        )
        return raw_token

    def confirm_reset(self, raw_token: str, new_password: str) -> None:
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(f"must be at least {MIN_PASSWORD_LENGTH} characters")

        token = self._reset_repo.find_valid_by_hash(_hash_token(raw_token))
        if token is None or not token.is_valid():
            raise InvalidOrExpiredTokenError("password reset token")

        user = self._user_repo.find_by_id(token.user_id)
        if user is None:
            raise InvalidOrExpiredTokenError("password reset token")

        user.set_password_hash(self._hasher.hash(new_password))
        self._user_repo.save(user)

        token.mark_used()
        self._reset_repo.mark_used(token.id)

        self._publisher.publish(
            UserEventType.PASSWORD_RESET_COMPLETED.value,
            UserEvent(event_type=UserEventType.PASSWORD_RESET_COMPLETED, user_id=user.id, payload={}),
        )
