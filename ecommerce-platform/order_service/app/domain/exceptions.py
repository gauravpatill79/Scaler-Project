class DomainError(Exception):
    http_status: int = 400


class OrderNotFoundError(DomainError):
    http_status = 404

    def __init__(self, order_id: str):
        super().__init__(f"Order '{order_id}' was not found")


class EmptyOrderError(DomainError):
    http_status = 409

    def __init__(self, user_id: str):
        super().__init__(f"Cannot place an order for user '{user_id}' with no items")


class InvalidOrderStateTransitionError(DomainError):
    http_status = 409

    def __init__(self, current: str, target: str):
        super().__init__(f"Cannot move an order from '{current}' to '{target}'")


class ProductNotPurchasableError(DomainError):
    http_status = 409

    def __init__(self, product_id: str):
        super().__init__(f"Product '{product_id}' is no longer available at checkout")


class CartServiceUnreachableError(DomainError):
    http_status = 503

    def __init__(self, user_id: str):
        super().__init__(f"Could not reach Cart Service to read the cart for user '{user_id}'")


class ProductCatalogUnreachableError(DomainError):
    http_status = 503

    def __init__(self, product_id: str):
        super().__init__(f"Could not reach Product Catalog Service to validate product '{product_id}'")
