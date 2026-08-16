import logging

import requests

from config import get_settings
from core.change_detection import DetectedChange
from db.models import Product, Snapshot
from notifications.base import NotificationChannel
from notifications.messages import (
    format_subject,
    format_plain_text,
)

logger = logging.getLogger(__name__)


class NtfyNotificationChannel(NotificationChannel):
    def __init__(self, destination: str) -> None:
        self.destination = destination

    def send(
        self, product: Product, snapshot: Snapshot, changes: list[DetectedChange]
    ) -> None:
        settings = get_settings()
        url = f"https://ntfy.sh/{self.destination}"
        headers = {
            "Title": format_subject(product, changes),
            "Content-Type": "text/plain; charset=utf-8",
        }
        body = format_plain_text(product, snapshot, changes)

        try:
            response = requests.post(
                url,
                data=body.encode("utf-8"),
                headers=headers,
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            logger.info(
                "Sent ntfy notification to topic %s for user_id=%s product_id=%s",
                self.destination,
                product.user_id,
                product.id,
            )
        except requests.RequestException as exc:
            logger.error(
                "Failed to send ntfy notification to topic %s for user_id=%s product_id=%s: %s",
                self.destination,
                product.user_id,
                product.id,
                exc,
            )
