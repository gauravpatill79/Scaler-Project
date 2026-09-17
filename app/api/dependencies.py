"""
Composition root: the one place that knows every concrete class. Everywhere
else in the codebase talks to interfaces (UserRepository, PasswordHasher,
EventPublisher, ...). Swapping MySQL for Postgres, or Kafka for SNS, means
editing only this file.
"""
from __future__ import annotations

from functools import lru_cache

from app.domain.enums import AuthProviderType
from app.infrastructure.messaging.event_publisher import EventPublisher, KafkaEventPublisher
from app.infrastructure.security.password_hasher import BcryptPasswordHasher, PasswordHasher
from app.infrastructure.security.token_service import JWTTokenService, TokenService
from app.repository.interfaces import (
    PasswordResetRepository,
    SocialAccountRepository,
    UserProfileRepository,
    UserRepository,
)
from app.repository.mysql_repository import (
    MySQLPasswordResetRepository,
    MySQLSocialAccountRepository,
    MySQLUserProfileRepository,
    MySQLUserRepository,
)
from app.services.auth_providers import AuthProvider, EmailPasswordAuthProvider, SocialAuthProvider
from app.services.auth_service import AuthService
from app.services.password_reset_service import PasswordResetService
from app.services.user_service import UserService


@lru_cache
def get_user_repository() -> UserRepository:
    return MySQLUserRepository()


@lru_cache
def get_profile_repository() -> UserProfileRepository:
    return MySQLUserProfileRepository()


@lru_cache
def get_social_repository() -> SocialAccountRepository:
    return MySQLSocialAccountRepository()


@lru_cache
def get_reset_repository() -> PasswordResetRepository:
    return MySQLPasswordResetRepository()


@lru_cache
def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    return JWTTokenService()


@lru_cache
def get_event_publisher() -> EventPublisher:
    return KafkaEventPublisher()


def _dummy_social_token_verifier(id_token: str) -> tuple[str, str]:
    """Placeholder — replace with real Google/Facebook/Apple SDK verification."""
    raise NotImplementedError("Wire up a real provider SDK here")


@lru_cache
def get_auth_providers() -> list[AuthProvider]:
    return [
        EmailPasswordAuthProvider(get_user_repository(), get_password_hasher()),
        SocialAuthProvider(
            AuthProviderType.GOOGLE, get_user_repository(), get_social_repository(), _dummy_social_token_verifier
        ),
    ]


def get_user_service() -> UserService:
    return UserService(
        get_user_repository(), get_profile_repository(), get_password_hasher(), get_event_publisher()
    )


def get_auth_service() -> AuthService:
    return AuthService(get_auth_providers(), get_token_service(), get_event_publisher())


def get_password_reset_service() -> PasswordResetService:
    return PasswordResetService(
        get_user_repository(), get_reset_repository(), get_password_hasher(), get_event_publisher()
    )
