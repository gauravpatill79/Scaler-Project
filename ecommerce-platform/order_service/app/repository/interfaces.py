from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import OrderStatus
from app.domain.models import Order


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order, previous_status: OrderStatus | None = None) -> None: ...

    @abstractmethod
    def find_by_id(self, order_id: str) -> Order | None: ...

    @abstractmethod
    def find_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Order]: ...
