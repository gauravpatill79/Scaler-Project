# Product Catalog Service — LLD

Implements PRD section 2 (Product Catalog: Browsing, Product Details, Search),
as the `Product Catalog Service` from the HLD. Language: Python 3.11+.
Framework: FastAPI. System of record: MySQL. Search: Elasticsearch. Events: Kafka.

## Layers

```
app/
  domain/          entities (Product, Category, ...), builders, enums, exceptions
  repository/       interfaces + mysql_repository.py (system of record)
  infrastructure/   db/ (MySQL), search/ (Elasticsearch adapter), messaging/ (Kafka)
  services/         ProductService, CategoryService, ProductSearchService
  api/              FastAPI routes, pydantic DTOs, dependency wiring (DI root)
```

## PRD requirement -> component map

| PRD ID | Requirement | Component |
|---|---|---|
| 2.1 | Browsing by category | `ProductService.list_by_category`, `CategoryService.get_tree` |
| 2.2 | Product details (images, description, specs) | `Product` entity + `ProductImage` / `ProductSpecification`, `ProductBuilder` |
| 2.3 | Search with keywords | `ProductSearchService` -> `ElasticsearchProductSearchAdapter` (fuzzy match for typo correction) |

## Design patterns used

- **Repository** — `ProductRepository` / `CategoryRepository` abstract MySQL access.
- **Adapter** — `ElasticsearchProductIndexer` / `ElasticsearchProductSearchAdapter`
  isolate the ES query DSL behind `SearchIndexer` / `ProductSearchPort` interfaces.
- **Builder** — `ProductBuilder` assembles a `Product` plus its images and
  specifications fluently, validating required fields at `.build()`.
- **Composite-style tree** — `Category.parent_id` self-reference, walked
  recursively by `CategoryService.get_tree`.
- **Singleton** — `Database.instance()`, one MySQL pool per process.
- **Observer / Pub-Sub** — `EventPublisher` -> Kafka, so Order/Cart Services
  learn about price and stock changes without a direct dependency.
- **DTO** — `api/schemas.py` pydantic models, separate from `domain/models.py`.
- **Dependency Injection** — every service receives interfaces via its
  constructor; `api/dependencies.py` is the sole composition root.

## SOLID

- **S**RP: `ProductService` (writes/lifecycle) is separate from `ProductSearchService`
  (reads) — they scale and fail independently.
- **O**CP: adding a new search backend means a new `ProductSearchPort` implementation, no service changes.
- **L**SP: `InMemorySearchIndexer` is a drop-in substitute for `ElasticsearchProductIndexer` in tests.
- **I**SP: `SearchIndexer` (write) and `ProductSearchPort` (read) are separate
  interfaces even though one class can implement both — consumers only depend on the half they need.
- **D**IP: services depend on `ProductRepository`, `SearchIndexer`, `EventPublisher`
  interfaces, never on `mysql.connector` or `elasticsearch` directly.

## MySQL <-> Elasticsearch consistency model

MySQL is authoritative and is the only write that can fail a request.
`ProductService.save()` calls to the repository are unguarded — if that
raises, the request correctly fails and nothing else runs. Every step after
that (`_safe_index`, `_safe_remove_from_index`, `_safe_publish`) is wrapped
in try/except: a broken Elasticsearch cluster or an unreachable Kafka broker
is logged with the product id and operation, then swallowed — it never
rolls back or fails a request that already has a durable, correct MySQL row.

This was verified directly: with both the search indexer and the event
publisher replaced by implementations that always raise `ConnectionError`,
`create_product`, `update_price`, `adjust_stock`, and `discontinue_product`
all still completed successfully and the MySQL-equivalent row was correctly
written and retrievable every time.

The trade-off is "read-your-writes on MySQL, eventually-consistent on
search" — a product can be briefly stale or missing in search/Kafka after a
write until the next update re-triggers indexing. There is no automatic
retry queue in this pass; the logged errors are the hook a reconciliation
job (or an on-call engineer re-running a re-index script) would use to catch
up. Call it out if you'd rather have a dedicated Kafka-consumer indexer with
its own retry/backoff for stricter decoupling.

## Kafka events published

| Event | Topic | Consumed by (future) |
|---|---|---|
| `product.created` | `product.created` | Search re-index workers, analytics |
| `product.updated` | `product.updated` | Search re-index workers |
| `product.price_changed` | `product.price_changed` | Cart Service (re-price active carts) |
| `product.stock_changed` | `product.stock_changed` | Cart Service (availability checks) |
| `product.discontinued` | `product.discontinued` | Cart/Order Services, search removal |

## Run locally

```bash
pip install -r requirements.txt
mysql -u root -p < app/infrastructure/db/schema.sql
export DB_HOST=localhost DB_USER=root DB_PASSWORD=yourpass DB_NAME=product_catalog_db
uvicorn app.main:app --reload
```

## Deliberate simplifications (call out before next service)

- `ProductService.adjust_stock` is exposed as a direct method; in production
  it's called from a Kafka consumer reacting to Order Service events (per the
  HLD flow), not a public HTTP endpoint — the route here is for
  admin/testing convenience.
- No pagination cursor / cache layer (Redis) in front of category browsing —
  HLD assigns Redis to Cart Service, so this is deferred there or added later if hot-path reads need it.
- Currency is a fixed `INR` default field, not a full multi-currency pricing model.
