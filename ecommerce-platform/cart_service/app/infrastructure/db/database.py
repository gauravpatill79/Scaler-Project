from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.collection import Collection


class Database:
    """Singleton — one MongoClient (which itself pools connections
    internally) per process."""

    _instance: "Database | None" = None

    def __init__(self):
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB_NAME", "cart_service_db")
        self._client: MongoClient = MongoClient(uri)
        self._db = self._client[db_name]

    @classmethod
    def instance(cls) -> "Database":
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    @property
    def carts(self) -> Collection:
        return self._db["carts"]
