from __future__ import annotations

import re

from app.domain.exceptions import CategoryNotFoundError
from app.domain.models import Category
from app.repository.interfaces import CategoryRepository


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class CategoryService:
    def __init__(self, repo: CategoryRepository):
        self._repo = repo

    def create_category(self, name: str, parent_id: str | None = None) -> Category:
        if parent_id is not None and self._repo.find_by_id(parent_id) is None:
            raise CategoryNotFoundError(parent_id)

        category = Category(name=name, slug=_slugify(name), parent_id=parent_id)
        self._repo.save(category)
        return category

    def get_category(self, category_id: str) -> Category:
        category = self._repo.find_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)
        return category

    def get_tree(self, root_id: str | None = None) -> dict:
        """Recursively builds a nested dict — the classic Composite read
        pattern for a category tree, without needing a Composite class
        hierarchy since Category has no behaviour that differs by depth."""
        children = self._repo.find_children(root_id)
        node_name = "root" if root_id is None else self.get_category(root_id).name
        return {
            "id": root_id,
            "name": node_name,
            "children": [self.get_tree(child.id) for child in children],
        }
