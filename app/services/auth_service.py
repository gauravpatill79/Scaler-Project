from __future__ import annotations

from app.domain.enums import AuthProviderType, UserEventType
from app.domain.exceptions import InvalidCredentialsError
from app.infrastructure.messaging.event_publisher import EventPublisher, UserEvent
from app.infrastructure.security.token_service import TokenService
from app.services.auth_providers import AuthProvider


class AuthService:
    def __init__(self, providers: list[AuthProvider], token_service: TokenService, publisher: EventPublisher):
        self._providers = providers
        self._tokens = token_service
        self._publisher = publisher

    def _resolve_provider(self, provider_type: AuthProviderType) -> AuthProvider:
        for provider in self._providers:
            if provider.supports(provider_type):
                return provider
        raise InvalidCredentialsError()

    def login(self, provider_type: AuthProviderType, credentials: dict) -> str:
        provider = self._resolve_provider(provider_type)
        user = provider.authenticate(credentials)
        user.ensure_active()

        access_token = self._tokens.issue_access_token(user)

        self._publisher.publish(
            UserEventType.USER_LOGGED_IN.value,
            UserEvent(event_type=UserEventType.USER_LOGGED_IN, user_id=user.id, payload={}),
        )
        return access_token
