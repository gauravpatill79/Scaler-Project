from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Cart


class CartRepository(ABC):
    @abstractmethod
    def save(self, cart: Cart) -> None: ...

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> Cart | None: ...

    @abstractmethod
    def delete(self, user_id: str) -> None: ...
