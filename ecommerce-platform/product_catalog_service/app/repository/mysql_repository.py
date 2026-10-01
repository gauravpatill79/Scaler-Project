from __future__ import annotations

from app.domain.enums import ProductStatus
from app.domain.models import Category, Product, ProductImage, ProductSpecification
from app.infrastructure.db.database import Database
from app.repository.interfaces import CategoryRepository, ProductRepository


class MySQLProductRepository(ProductRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    # ---- writes ----

    def save(self, product: Product) -> None:
        query = """
            INSERT INTO products (id, sku, name, description, price, currency,
                                   category_id, status, stock_quantity, created_at, updated_at)
            VALUES (%(id)s, %(sku)s, %(name)s, %(description)s, %(price)s, %(currency)s,
                    %(category_id)s, %(status)s, %(stock_quantity)s, %(created_at)s, %(updated_at)s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name), description = VALUES(description), price = VALUES(price),
                category_id = VALUES(category_id), status = VALUES(status),
                stock_quantity = VALUES(stock_quantity), updated_at = VALUES(updated_at)
        """
        params = {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "currency": product.currency,
            "category_id": product.category_id,
            "status": product.status.value,
            "stock_quantity": product.stock_quantity,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            cursor.execute("DELETE FROM product_images WHERE product_id = %s", (product.id,))
            for image in product.images:
                cursor.execute(
                    """INSERT INTO product_images (id, product_id, url, is_primary, sort_order)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (image.id, product.id, image.url, image.is_primary, image.sort_order),
                )

            cursor.execute("DELETE FROM product_specifications WHERE product_id = %s", (product.id,))
            for spec in product.specifications:
                cursor.execute(
                    """INSERT INTO product_specifications (id, product_id, spec_key, spec_value)
                       VALUES (UUID(), %s, %s, %s)""",
                    (product.id, spec.spec_key, spec.spec_value),
                )
            cursor.close()

    # ---- reads ----

    def _hydrate(self, conn, row: dict) -> Product:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM product_images WHERE product_id = %s ORDER BY sort_order", (row["id"],)
        )
        images = [ProductImage(**img) for img in cursor.fetchall()]

        cursor.execute(
            "SELECT product_id, spec_key, spec_value FROM product_specifications WHERE product_id = %s",
            (row["id"],),
        )
        specs = [ProductSpecification(**s) for s in cursor.fetchall()]
        cursor.close()

        return Product(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            description=row["description"] or "",
            price=row["price"],
            currency=row["currency"],
            category_id=row["category_id"],
            status=ProductStatus(row["status"]),
            stock_quantity=row["stock_quantity"],
            images=images,
            specifications=specs,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def find_by_id(self, product_id: str) -> Product | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            row = cursor.fetchone()
            cursor.close()
            return self._hydrate(conn, row) if row else None

    def find_by_sku(self, sku: str) -> Product | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE sku = %s", (sku,))
            row = cursor.fetchone()
            cursor.close()
            return self._hydrate(conn, row) if row else None

    def find_by_category(self, category_id: str, limit: int = 50, offset: int = 0) -> list[Product]:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT * FROM products WHERE category_id = %s AND status != 'DISCONTINUED'
                   ORDER BY created_at DESC LIMIT %s OFFSET %s""",
                (category_id, limit, offset),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [self._hydrate(conn, row) for row in rows]

    def exists_by_sku(self, sku: str) -> bool:
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM products WHERE sku = %s LIMIT 1", (sku,))
            found = cursor.fetchone() is not None
            cursor.close()
        return found


class MySQLCategoryRepository(CategoryRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, category: Category) -> None:
        query = """
            INSERT INTO categories (id, name, slug, parent_id)
            VALUES (%(id)s, %(name)s, %(slug)s, %(parent_id)s)
            ON DUPLICATE KEY UPDATE name = VALUES(name), parent_id = VALUES(parent_id)
        """
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, vars(category))
            cursor.close()

    def find_by_id(self, category_id: str) -> Category | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, slug, parent_id FROM categories WHERE id = %s", (category_id,)
            )
            row = cursor.fetchone()
            cursor.close()
        return Category(**row) if row else None

    def find_children(self, parent_id: str | None) -> list[Category]:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            if parent_id is None:
                cursor.execute("SELECT id, name, slug, parent_id FROM categories WHERE parent_id IS NULL")
            else:
                cursor.execute(
                    "SELECT id, name, slug, parent_id FROM categories WHERE parent_id = %s", (parent_id,)
                )
            rows = cursor.fetchall()
            cursor.close()
        return [Category(**row) for row in rows]
