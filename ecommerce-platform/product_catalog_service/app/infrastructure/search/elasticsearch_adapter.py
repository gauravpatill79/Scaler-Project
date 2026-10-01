"""
Adapter pattern: Elasticsearch's query DSL never leaks past this module.
`ProductService` and `ProductSearchService` only see `SearchIndexer` /
`ProductSearchPort` interfaces, so swapping Elasticsearch for OpenSearch or
Algolia later touches only this file.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Product

INDEX_NAME = "products"


class SearchIndexer(ABC):
    """Write side — keeps the ES index in sync with MySQL."""

    @abstractmethod
    def index(self, product: Product) -> None: ...

    @abstractmethod
    def remove(self, product_id: str) -> None: ...


class ProductSearchPort(ABC):
    """Read side — full-text + faceted search used by the search bar (2.3)."""

    @abstractmethod
    def search(
        self, query: str, category_id: str | None = None, limit: int = 20, offset: int = 0
    ) -> list[dict]: ...


def _to_document(product: Product) -> dict:
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "currency": product.currency,
        "category_id": product.category_id,
        "status": product.status.value,
        "in_stock": product.stock_quantity > 0,
        "image_url": product.primary_image_url(),
        "specifications": {s.spec_key: s.spec_value for s in product.specifications},
    }


class ElasticsearchProductIndexer(SearchIndexer):
    def __init__(self, hosts: list[str] | None = None):
        from elasticsearch import Elasticsearch  # lazy import — optional at unit-test time

        self._client = Elasticsearch(hosts or ["http://localhost:9200"])

    def index(self, product: Product) -> None:
        self._client.index(index=INDEX_NAME, id=product.id, document=_to_document(product))

    def remove(self, product_id: str) -> None:
        self._client.delete(index=INDEX_NAME, id=product_id, ignore=[404])


class ElasticsearchProductSearchAdapter(ProductSearchPort):
    def __init__(self, hosts: list[str] | None = None):
        from elasticsearch import Elasticsearch

        self._client = Elasticsearch(hosts or ["http://localhost:9200"])

    def search(
        self, query: str, category_id: str | None = None, limit: int = 20, offset: int = 0
    ) -> list[dict]:
        must: list[dict] = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description", "specifications.*"],
                    "fuzziness": "AUTO",  # typo correction (2.3)
                }
            }
        ]
        filters = [{"term": {"status": "ACTIVE"}}]
        if category_id:
            filters.append({"term": {"category_id": category_id}})

        body = {
            "query": {"bool": {"must": must, "filter": filters}},
            "from": offset,
            "size": limit,
        }
        response = self._client.search(index=INDEX_NAME, body=body)
        return [hit["_source"] for hit in response["hits"]["hits"]]


class InMemorySearchIndexer(SearchIndexer, ProductSearchPort):
    """Test double combining both ports — good enough for unit tests that
    don't need real relevance scoring, just presence/absence checks."""

    def __init__(self):
        self._docs: dict[str, dict] = {}

    def index(self, product: Product) -> None:
        self._docs[product.id] = _to_document(product)

    def remove(self, product_id: str) -> None:
        self._docs.pop(product_id, None)

    def search(
        self, query: str, category_id: str | None = None, limit: int = 20, offset: int = 0
    ) -> list[dict]:
        results = [
            doc
            for doc in self._docs.values()
            if doc["status"] == "ACTIVE" and query.lower() in doc["name"].lower()
            and (category_id is None or doc["category_id"] == category_id)
        ]
        return results[offset: offset + limit]
