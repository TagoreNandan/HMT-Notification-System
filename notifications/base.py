from abc import ABC, abstractmethod

from core.change_detection import DetectedChange
from db.models import Product, Snapshot


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, product: Product, snapshot: Snapshot, changes: list[DetectedChange]) -> None:
        ...
