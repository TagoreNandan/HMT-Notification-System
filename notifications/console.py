import logging
from typing import Any

from events.models import NotificationEvent
from notifications.base import NotificationChannel

logger = logging.getLogger(__name__)


class ConsoleNotificationChannel(NotificationChannel):
    def __init__(self, destination: str | None = None) -> None:
        self.destination = destination

    def send(
        self,
        event_or_product: Any,
        snapshot: Any = None,
        changes: Any = None,
    ) -> None:
        if isinstance(event_or_product, NotificationEvent):
            evt = event_or_product
            logger.warning(
                "CONSOLE ALERT [%s] product_id=%s title=%r url=%s price=%s in_stock=%s | %s -> %s | details=%s",
                evt.event_type,
                evt.product_id,
                evt.title,
                evt.url,
                evt.price,
                evt.in_stock,
                evt.old_value,
                evt.new_value,
                evt.details,
            )
            return

        product = event_or_product
        actionable = [
            c for c in (changes or []) if getattr(c, "change_type", None) != "no_change"
        ]
        if not actionable:
            logger.info(
                "No changes for product id=%s url=%s",
                getattr(product, "id", None),
                getattr(product, "url", None),
            )
            return

        for change in actionable:
            logger.warning(
                "CHANGE [%s] user_id=%s product_id=%s title=%r url=%s | %s -> %s",
                getattr(change.change_type, "value", change.change_type),
                getattr(product, "user_id", None),
                getattr(product, "id", None),
                getattr(snapshot, "title", None) or getattr(product, "title", None),
                getattr(product, "url", None),
                getattr(change, "old_value", None),
                getattr(change, "new_value", None),
            )
