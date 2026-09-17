"""
Observer / Publish-Subscribe pattern: this service never talks to Notification
Service, Order Service, etc. directly. It publishes a fact ("user registered")
to Kafka and any number of downstream consumers react independently. This
keeps User Management Service decoupled from every future subscriber.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from app.domain.enums import UserEventType


@dataclass
class UserEvent:
    event_type: UserEventType
    user_id: str
    payload: dict
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self) -> str:
        body = asdict(self)
        body["event_type"] = self.event_type.value
        body["occurred_at"] = self.occurred_at.isoformat()
        return json.dumps(body)


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, topic: str, event: UserEvent) -> None: ...


class KafkaEventPublisher(EventPublisher):
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        from kafka import KafkaProducer  # imported lazily so unit tests don't need kafka installed

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: v.encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )

    def publish(self, topic: str, event: UserEvent) -> None:
        # Key by user_id so all events for one user land on the same partition,
        # preserving per-user ordering for downstream consumers.
        self._producer.send(topic, key=event.user_id, value=event.to_json())
        self._producer.flush()


class InMemoryEventPublisher(EventPublisher):
    """Test double — captures events instead of hitting a real broker."""

    def __init__(self):
        self.published: list[tuple[str, UserEvent]] = []

    def publish(self, topic: str, event: UserEvent) -> None:
        self.published.append((topic, event))
