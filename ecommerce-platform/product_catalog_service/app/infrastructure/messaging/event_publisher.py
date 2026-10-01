from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from app.domain.enums import ProductEventType


@dataclass
class ProductEvent:
    event_type: ProductEventType
    product_id: str
    payload: dict
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self) -> str:
        body = asdict(self)
        body["event_type"] = self.event_type.value
        body["occurred_at"] = self.occurred_at.isoformat()
        return json.dumps(body)


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, topic: str, event: ProductEvent) -> None: ...


class KafkaEventPublisher(EventPublisher):
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        from kafka import KafkaProducer

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: v.encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )

    def publish(self, topic: str, event: ProductEvent) -> None:
        self._producer.send(topic, key=event.product_id, value=event.to_json())
        self._producer.flush()


class InMemoryEventPublisher(EventPublisher):
    def __init__(self):
        self.published: list[tuple[str, ProductEvent]] = []

    def publish(self, topic: str, event: ProductEvent) -> None:
        self.published.append((topic, event))
