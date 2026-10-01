"""
Singleton pattern: exactly one connection pool per process. Every repository
pulls connections from here instead of opening its own — cheap to test
(swap out `Database._instance`) and cheap on the DB (bounded pool size).
"""
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
            pool_name="user_mgmt_pool",
            pool_size=pool_size,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "user_management_db"),
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
            conn.close()  # returns the connection to the pool
