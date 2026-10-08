from __future__ import annotations

from app.domain.enums import OrderStatus
from app.domain.models import Order, OrderItem, ShippingAddress
from app.infrastructure.db.database import Database
from app.repository.interfaces import OrderRepository


class MySQLOrderRepository(OrderRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, order: Order, previous_status: OrderStatus | None = None) -> None:
        query = """
            INSERT INTO orders (id, user_id, status, total_amount, currency, payment_method, tracking_number,
                                 address_line1, address_line2, address_city, address_state,
                                 address_postal_code, address_country, created_at, updated_at)
            VALUES (%(id)s, %(user_id)s, %(status)s, %(total_amount)s, %(currency)s, %(payment_method)s,
                    %(tracking_number)s, %(line1)s, %(line2)s, %(city)s, %(state)s, %(postal_code)s,
                    %(country)s, %(created_at)s, %(updated_at)s)
            ON DUPLICATE KEY UPDATE
                status = VALUES(status), tracking_number = VALUES(tracking_number),
                updated_at = VALUES(updated_at)
        """
        params = {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status.value,
            "total_amount": order.total(),
            "currency": order.currency,
            "payment_method": order.payment_method,
            "tracking_number": order.tracking_number,
            "line1": order.address.line1,
            "line2": order.address.line2,
            "city": order.address.city,
            "state": order.address.state,
            "postal_code": order.address.postal_code,
            "country": order.address.country,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            cursor.execute("SELECT 1 FROM order_items WHERE order_id = %s LIMIT 1", (order.id,))
            if cursor.fetchone() is None:
                for item in order.items:
                    cursor.execute(
                        """INSERT INTO order_items (id, order_id, product_id, name_snapshot,
                                                      price_snapshot, quantity)
                           VALUES (UUID(), %s, %s, %s, %s, %s)""",
                        (order.id, item.product_id, item.name_snapshot, item.price_snapshot, item.quantity),
                    )

            cursor.execute(
                """INSERT INTO order_status_history (id, order_id, from_status, to_status, changed_at)
                   VALUES (UUID(), %s, %s, %s, %s)""",
                (
                    order.id,
                    previous_status.value if previous_status else None,
                    order.status.value,
                    order.updated_at,
                ),
            )
            cursor.close()

    def _hydrate(self, conn, row: dict) -> Order:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT product_id, name_snapshot, price_snapshot, quantity FROM order_items WHERE order_id = %s",
            (row["id"],),
        )
        items = [OrderItem(**item_row) for item_row in cursor.fetchall()]
        cursor.close()

        address = ShippingAddress(
            line1=row["address_line1"],
            line2=row["address_line2"],
            city=row["address_city"],
            state=row["address_state"],
            postal_code=row["address_postal_code"],
            country=row["address_country"],
        )
        return Order(
            id=row["id"],
            user_id=row["user_id"],
            items=items,
            address=address,
            payment_method=row["payment_method"],
            status=OrderStatus(row["status"]),
            currency=row["currency"],
            tracking_number=row["tracking_number"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def find_by_id(self, order_id: str) -> Order | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            row = cursor.fetchone()
            cursor.close()
            return self._hydrate(conn, row) if row else None

    def find_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Order]:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [self._hydrate(conn, row) for row in rows]
