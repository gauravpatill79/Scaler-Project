"""
Strategy pattern: AuthService holds a list of AuthProvider strategies and
picks the one matching the request. Adding Apple/Facebook login later means
adding a new class here — AuthService itself never changes (Open/Closed
Principle).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import AuthProviderType
from app.domain.exceptions import InvalidCredentialsError
from app.domain.models import SocialAccount, User
from app.infrastructure.security.password_hasher import PasswordHasher
from app.repository.interfaces import SocialAccountRepository, UserRepository


class AuthProvider(ABC):
    provider_type: AuthProviderType

    @abstractmethod
    def supports(self, provider_type: AuthProviderType) -> bool: ...

    @abstractmethod
    def authenticate(self, credentials: dict) -> User: ...


class EmailPasswordAuthProvider(AuthProvider):
    provider_type = AuthProviderType.EMAIL_PASSWORD

    def __init__(self, user_repo: UserRepository, hasher: PasswordHasher):
        self._user_repo = user_repo
        self._hasher = hasher

    def supports(self, provider_type: AuthProviderType) -> bool:
        return provider_type == self.provider_type

    def authenticate(self, credentials: dict) -> User:
        email = credentials["email"]
        raw_password = credentials["password"]

        user = self._user_repo.find_by_email(email)
        if user is None or user.password_hash is None:
            raise InvalidCredentialsError()

        if not self._hasher.verify(raw_password, user.password_hash):
            user.record_failed_login()
            self._user_repo.save(user)
            raise InvalidCredentialsError()

        user.record_successful_login()
        self._user_repo.save(user)
        return user


class SocialAuthProvider(AuthProvider):
    """Handles GOOGLE / FACEBOOK / APPLE — the id-token verification step
    differs per network but the resulting flow (find-or-link account) is
    identical, so it's parameterised by provider_type instead of subclassed
    per network.
    """

    def __init__(
        self,
        provider_type: AuthProviderType,
        user_repo: UserRepository,
        social_repo: SocialAccountRepository,
        token_verifier,
    ):
        self.provider_type = provider_type
        self._user_repo = user_repo
        self._social_repo = social_repo
        self._verify_external_token = token_verifier  # injected callable per network's SDK

    def supports(self, provider_type: AuthProviderType) -> bool:
        return provider_type == self.provider_type

    def authenticate(self, credentials: dict) -> User:
        external_id, email = self._verify_external_token(credentials["id_token"])

        link = self._social_repo.find_by_provider_id(self.provider_type.value, external_id)
        if link is not None:
            user = self._user_repo.find_by_id(link.user_id)
            if user is None:
                raise InvalidCredentialsError()
            user.record_successful_login()
            self._user_repo.save(user)
            return user

        # First-time social login: find existing account by email, or create one.
        user = self._user_repo.find_by_email(email)
        if user is None:
            user = User(email=email)
            user.activate()  # social providers already verified the email
            self._user_repo.save(user)

        self._social_repo.save(
            SocialAccount(user_id=user.id, provider=self.provider_type, provider_user_id=external_id)
        )
        user.record_successful_login()
        self._user_repo.save(user)
        return user
