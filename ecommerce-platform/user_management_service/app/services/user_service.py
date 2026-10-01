"""
Application service (use-case layer). Orchestrates domain objects,
repositories, and infrastructure — but contains no SQL and no HTTP concerns
(Single Responsibility Principle). Every dependency is injected as an
interface (Dependency Inversion) so this class is unit-testable with fakes.
"""
from __future__ import annotations

from app.domain.enums import UserEventType
from app.domain.exceptions import UserAlreadyExistsError, UserNotFoundError, WeakPasswordError
from app.domain.models import User, UserProfile
from app.infrastructure.messaging.event_publisher import EventPublisher, UserEvent
from app.infrastructure.security.password_hasher import PasswordHasher
from app.repository.interfaces import UserProfileRepository, UserRepository

MIN_PASSWORD_LENGTH = 8


class UserFactory:
    """Factory pattern: centralises the invariants of "what does a brand-new
    user look like" so UserService.register doesn't hand-assemble entities.
    """

    def __init__(self, hasher: PasswordHasher):
        self._hasher = hasher

    def create(self, email: str, raw_password: str) -> User:
        if len(raw_password) < MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(f"must be at least {MIN_PASSWORD_LENGTH} characters")

        user = User(email=email.strip().lower())
        user.set_password_hash(self._hasher.hash(raw_password))
        return user


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        profile_repo: UserProfileRepository,
        hasher: PasswordHasher,
        publisher: EventPublisher,
        user_factory: UserFactory | None = None,
    ):
        self._user_repo = user_repo
        self._profile_repo = profile_repo
        self._publisher = publisher
        self._factory = user_factory or UserFactory(hasher)

    def register(self, email: str, raw_password: str, first_name: str = "", last_name: str = "") -> User:
        if self._user_repo.exists_by_email(email):
            raise UserAlreadyExistsError(email)

        user = self._factory.create(email, raw_password)
        user.activate()  # simplified: email verification flow omitted from this LLD pass
        self._user_repo.save(user)

        profile = UserProfile(user_id=user.id, first_name=first_name, last_name=last_name)
        self._profile_repo.save(profile)

        self._publisher.publish(
            UserEventType.USER_REGISTERED.value,
            UserEvent(
                event_type=UserEventType.USER_REGISTERED,
                user_id=user.id,
                payload={"email": user.email},
            ),
        )
        return user

    def get_profile(self, user_id: str) -> UserProfile:
        profile = self._profile_repo.find_by_user_id(user_id)
        if profile is None:
            raise UserNotFoundError(user_id)
        return profile

    def update_profile(self, user_id: str, **fields) -> UserProfile:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        profile = self._profile_repo.find_by_user_id(user_id) or UserProfile(user_id=user_id)
        profile.update(**fields)
        self._profile_repo.save(profile)

        self._publisher.publish(
            UserEventType.USER_PROFILE_UPDATED.value,
            UserEvent(event_type=UserEventType.USER_PROFILE_UPDATED, user_id=user_id, payload=fields),
        )
        return profile
