# Cart Service — LLD

Implements PRD section 3 (Cart & Checkout: add to cart, cart review, the
cart side of checkout), as the `Cart Service` from the HLD. Language:
Python 3.11+. Framework: FastAPI. System of record: MongoDB. Cache: Redis.
Events: Kafka. Depends on Product Catalog Service over HTTP.

## Layers

```
app/
  domain/          Cart (aggregate root), CartItem, enums, exceptions
  repository/       interfaces + mongo_repository.py (system of record)
  infrastructure/   db/ (MongoDB), cache/ (Redis), clients/ (Product Catalog HTTP adapter), messaging/ (Kafka)
  services/         CartService — cache-aside orchestration
  api/              FastAPI routes, pydantic DTOs, dependency wiring (DI root)
```

## PRD requirement -> component map

| PRD ID | Requirement | Component |
|---|---|---|
| 3.1 | Add to cart | `CartService.add_item` — validates against Product Catalog Service first |
| 3.2 | Cart review (items, price, quantity, total) | `Cart.subtotal()`, `Cart.item_count()`, `GET /carts/{user_id}` |
| 3.3 | Checkout (cart side) | `CartService.mark_checked_out` — Order Management Service calls this to start checkout |

## Design patterns used

- **Aggregate root (DDD)** — `Cart` owns all mutation of its `CartItem`
  list; invariants (one entry per product, quantity >= 1) are enforced in
  one place, not scattered across the service layer.
- **Repository** — `CartRepository` abstracts MongoDB; `MongoCartRepository` is the implementation.
- **Cache-Aside** — `CartCache` (Redis) sits in front of `CartRepository`.
  Reads check cache first, fall back to Mongo on a miss, then repopulate the
  cache. Writes always go to Mongo first, then refresh the cache.
- **Adapter / Anti-Corruption Layer** — `ProductCatalogClient` isolates
  Cart Service's domain model from Product Catalog Service's HTTP response
  shape; only `HttpProductCatalogClient` knows about HTTP status codes or JSON field names.
- **Observer / Pub-Sub** — `EventPublisher` -> Kafka, matching the HLD's
  "Cart Service produces a message to Kafka" flow (Part 2).
- **DTO** — `api/schemas.py` pydantic models, separate from `domain/models.py`.
- **Dependency Injection** — every service receives interfaces via its
  constructor; `api/dependencies.py` is the sole composition root.

## SOLID

- **S**RP: `CartService` handles cart mutation only — product validity
  lives in Product Catalog Service, reached through `ProductCatalogClient`, not duplicated here.
- **O**CP: swapping Redis for Memcached, or MongoDB for DynamoDB, means a
  new `CartCache` / `CartRepository` implementation, no service changes.
- **L**SP: `InMemoryCartCache` and `InMemoryProductCatalogClient` are
  drop-in substitutes for their real implementations in tests.
- **I**SP: `CartCache` (3 methods) and `ProductCatalogClient` (1 method)
  stay narrow and specific to what `CartService` actually needs.
- **D**IP: `CartService` depends on `CartRepository`, `CartCache`,
  `ProductCatalogClient`, `EventPublisher` interfaces, never on `pymongo`, `redis`, or `httpx` directly.

## Resilience: Mongo is the only write that can fail a request

Same pattern as Product Catalog Service. `CartService` calls
`self._repo.save(cart)` unguarded — if that raises, the request correctly
fails. Every cache write/invalidate and every Kafka publish is wrapped in
try/except and logged, never raised. `get_cart` also catches a cache read
failure and falls back to Mongo directly.

This was verified directly: with both the cache and the event publisher
replaced by implementations that always raise `ConnectionError`,
`add_item`, `get_cart`, `update_quantity`, and `mark_checked_out` all
completed successfully using the Mongo-equivalent store as the source of truth.

## Price snapshotting

`CartItem.price_snapshot` is captured at add-time from Product Catalog
Service and refreshed every time the same product is added again. This
means a cart can briefly hold a stale price if the catalog price changes
between add-to-cart and checkout. Order Management Service is expected to
re-validate price and stock against Product Catalog Service at checkout
time rather than trusting the cart snapshot as final — this is called out
here so that re-validation isn't skipped when Order Service is built.

## Kafka events published

| Event | Topic | Consumed by (future) |
|---|---|---|
| `cart.item_added` | `cart.item_added` | Analytics, abandoned-cart reminders |
| `cart.item_removed` | `cart.item_removed` | Analytics |
| `cart.item_quantity_updated` | `cart.item_quantity_updated` | Analytics |
| `cart.cleared` | `cart.cleared` | Analytics |
| `cart.checked_out` | `cart.checked_out` | Order Management Service |

## Run locally

```bash
pip install -r requirements.txt
mongosh cart_service_db app/infrastructure/db/mongo_init.js
export MONGO_URI=mongodb://localhost:27017 MONGO_DB_NAME=cart_service_db
export REDIS_HOST=localhost
export PRODUCT_CATALOG_SERVICE_URL=http://localhost:8002
uvicorn app.main:app --reload --port 8003
```

## Deliberate simplifications

- No abandoned-cart cleanup job in this pass — `mongo_init.js` creates the
  `{status, updated_at}` index such a job would need, but the job itself
  (an hourly consumer marking old `ACTIVE` carts as `ABANDONED`) is not built here.
- `mark_checked_out` only flips cart status and publishes an event; actual
  order creation, stock reservation, and payment are Order Management
  Service's responsibility once that service exists.
- Cart-merge-on-login (anonymous cart + authenticated cart reconciliation)
  is out of scope for this pass — `user_id` is assumed to already be a
  resolved, authenticated identity by the time requests reach this service.
