from abc import ABC, abstractmethod
from typing import Any

from events.models import NotificationEvent


class NotificationChannel(ABC):
    @abstractmethod
    def send(
        self,
        event_or_product: NotificationEvent | Any,
        snapshot: Any = None,
        changes: Any = None,
    ) -> None: ...
