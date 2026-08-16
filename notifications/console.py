import logging

from core.change_detection import ChangeType, DetectedChange
from db.models import Product, Snapshot
from notifications.base import NotificationChannel

logger = logging.getLogger(__name__)


class ConsoleNotificationChannel(NotificationChannel):
    def send(
        self, product: Product, snapshot: Snapshot, changes: list[DetectedChange]
    ) -> None:
        actionable = [c for c in changes if c.change_type != ChangeType.NO_CHANGE]
        if not actionable:
            logger.info(
                "No changes for user_id=%s product id=%s url=%s title=%r price=%s in_stock=%s",
                product.user_id,
                product.id,
                product.url,
                snapshot.title,
                snapshot.price,
                snapshot.in_stock,
            )
            return

        for change in actionable:
            logger.warning(
                "CHANGE [%s] user_id=%s product_id=%s title=%r url=%s | %s -> %s | details=%s",
                change.change_type.value,
                product.user_id,
                product.id,
                snapshot.title,
                product.url,
                change.old_value,
                change.new_value,
                change.details,
            )
