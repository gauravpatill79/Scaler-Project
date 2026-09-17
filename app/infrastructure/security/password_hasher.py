from __future__ import annotations

from abc import ABC, abstractmethod

import bcrypt


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, raw_password: str) -> str: ...

    @abstractmethod
    def verify(self, raw_password: str, hashed: str) -> bool: ...


class BcryptPasswordHasher(PasswordHasher):
    def __init__(self, rounds: int = 12):
        self._rounds = rounds

    def hash(self, raw_password: str) -> str:
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, raw_password: str, hashed: str) -> bool:
        return bcrypt.checkpw(raw_password.encode("utf-8"), hashed.encode("utf-8"))
