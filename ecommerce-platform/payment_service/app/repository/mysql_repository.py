from __future__ import annotations

from app.domain.enums import PaymentMethod, PaymentStatus
from app.domain.models import Payment
from app.infrastructure.db.database import Database
from app.repository.interfaces import PaymentRepository


def _row_to_payment(row: dict) -> Payment:
    return Payment(
        id=row["id"],
        order_id=row["order_id"],
        user_id=row["user_id"],
        amount=row["amount"],
        currency=row["currency"],
        method=PaymentMethod(row["method"]),
        status=PaymentStatus(row["status"]),
        gateway_reference=row["gateway_reference"],
        receipt_number=row["receipt_number"],
        failure_reason=row["failure_reason"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class MySQLPaymentRepository(PaymentRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, payment: Payment, previous_status: PaymentStatus | None = None) -> None:
        query = """
            INSERT INTO payments (id, order_id, user_id, amount, currency, method, status,
                                   gateway_reference, receipt_number, failure_reason,
                                   created_at, updated_at)
            VALUES (%(id)s, %(order_id)s, %(user_id)s, %(amount)s, %(currency)s, %(method)s, %(status)s,
                    %(gateway_reference)s, %(receipt_number)s, %(failure_reason)s,
                    %(created_at)s, %(updated_at)s)
            ON DUPLICATE KEY UPDATE
                status = VALUES(status), gateway_reference = VALUES(gateway_reference),
                receipt_number = VALUES(receipt_number), failure_reason = VALUES(failure_reason),
                updated_at = VALUES(updated_at)
        """
        params = {
            "id": payment.id,
            "order_id": payment.order_id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "method": payment.method.value,
            "status": payment.status.value,
            "gateway_reference": payment.gateway_reference,
            "receipt_number": payment.receipt_number,
            "failure_reason": payment.failure_reason,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
        }
        with self._db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            cursor.execute(
                """INSERT INTO payment_transactions (id, payment_id, from_status, to_status, detail, changed_at)
                   VALUES (UUID(), %s, %s, %s, %s, %s)""",
                (
                    payment.id,
                    previous_status.value if previous_status else None,
                    payment.status.value,
                    payment.gateway_reference or payment.failure_reason,
                    payment.updated_at,
                ),
            )
            cursor.close()

    def find_by_id(self, payment_id: str) -> Payment | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
            row = cursor.fetchone()
            cursor.close()
        return _row_to_payment(row) if row else None

    def find_by_order_id(self, order_id: str) -> Payment | None:
        with self._db.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM payments WHERE order_id = %s", (order_id,))
            row = cursor.fetchone()
            cursor.close()
        return _row_to_payment(row) if row else None
