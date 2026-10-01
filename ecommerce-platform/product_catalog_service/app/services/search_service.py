from __future__ import annotations

from app.infrastructure.search.elasticsearch_adapter import ProductSearchPort


class ProductSearchService:
    """Thin orchestration layer over the search port. Kept separate from
    ProductService (SRP) since search is a read-only concern with its own
    scaling/caching characteristics, independent of catalog writes."""

    def __init__(self, search_port: ProductSearchPort):
        self._search_port = search_port

    def search(self, query: str, category_id: str | None = None, page: int = 1, page_size: int = 20) -> list[dict]:
        offset = max(page - 1, 0) * page_size
        return self._search_port.search(query, category_id=category_id, limit=page_size, offset=offset)
