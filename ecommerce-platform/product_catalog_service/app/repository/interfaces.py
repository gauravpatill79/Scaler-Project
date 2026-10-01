from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Category, Product


class ProductRepository(ABC):
    @abstractmethod
    def save(self, product: Product) -> None: ...

    @abstractmethod
    def find_by_id(self, product_id: str) -> Product | None: ...

    @abstractmethod
    def find_by_sku(self, sku: str) -> Product | None: ...

    @abstractmethod
    def find_by_category(self, category_id: str, limit: int = 50, offset: int = 0) -> list[Product]: ...

    @abstractmethod
    def exists_by_sku(self, sku: str) -> bool: ...


class CategoryRepository(ABC):
    @abstractmethod
    def save(self, category: Category) -> None: ...

    @abstractmethod
    def find_by_id(self, category_id: str) -> Category | None: ...

    @abstractmethod
    def find_children(self, parent_id: str | None) -> list[Category]: ...
