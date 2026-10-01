from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

import jwt

from app.domain.exceptions import InvalidOrExpiredTokenError
from app.domain.models import User


class TokenService(ABC):
    @abstractmethod
    def issue_access_token(self, user: User) -> str: ...

    @abstractmethod
    def decode(self, token: str) -> dict: ...


class JWTTokenService(TokenService):
    """Stateless auth tokens. Session revocation, if needed, is handled by
    checking the `user_sessions` table for refresh tokens — access tokens
    stay short-lived (see ACCESS_TOKEN_TTL_MIN) so revocation lag is bounded.
    """

    def __init__(self, secret: str | None = None, algorithm: str = "HS256", ttl_minutes: int = 30):
        self._secret = secret or os.getenv("JWT_SECRET", "change-me-in-production")
        self._algorithm = algorithm
        self._ttl_minutes = ttl_minutes

    def issue_access_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.id,
            "email": user.email,
            "status": user.status.value,
            "iat": now,
            "exp": now + timedelta(minutes=self._ttl_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidOrExpiredTokenError("access token") from exc
