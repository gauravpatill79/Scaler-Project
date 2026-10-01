from enum import Enum


class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class ProductEventType(str, Enum):
    """Kafka event topics this service publishes. Order/Cart Services
    subscribe to these to react to price and availability changes."""
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_PRICE_CHANGED = "product.price_changed"
    PRODUCT_STOCK_CHANGED = "product.stock_changed"
    PRODUCT_DISCONTINUED = "product.discontinued"
