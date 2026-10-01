"""
Repository pattern + Interface Segregation: each interface exposes only the
methods its consumers actually need, and services depend on these
abstractions (DIP) rather than on MySQLConnector directly. Any storage engine
can be swapped in by implementing these ABCs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import PasswordResetToken, SocialAccount, User, UserProfile


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    def find_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool: ...


class UserProfileRepository(ABC):
    @abstractmethod
    def save(self, profile: UserProfile) -> None: ...

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> UserProfile | None: ...


class SocialAccountRepository(ABC):
    @abstractmethod
    def save(self, account: SocialAccount) -> None: ...

    @abstractmethod
    def find_by_provider_id(self, provider: str, provider_user_id: str) -> SocialAccount | None: ...


class PasswordResetRepository(ABC):
    @abstractmethod
    def save(self, token: PasswordResetToken) -> None: ...

    @abstractmethod
    def find_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None: ...

    @abstractmethod
    def mark_used(self, token_id: str) -> None: ...
