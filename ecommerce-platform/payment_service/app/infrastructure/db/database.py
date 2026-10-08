from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool


class Database:
    _instance: "Database | None" = None

    def __init__(self, pool_size: int = 10):
        self._pool = MySQLConnectionPool(
            pool_name="payment_service_pool",
            pool_size=pool_size,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "payment_service_db"),
            autocommit=False,
        )

    @classmethod
    def instance(cls) -> "Database":
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    @contextmanager
    def connection(self) -> Iterator[mysql.connector.MySQLConnection]:
        conn = self._pool.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
