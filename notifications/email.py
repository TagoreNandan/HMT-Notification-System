import logging

import requests

from config import get_settings
from core.change_detection import DetectedChange
from db.models import Product, Snapshot
from notifications.base import NotificationChannel
from notifications.messages import (
    format_subject,
    format_plain_text,
    format_html,
)

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailNotificationChannel(NotificationChannel):
    def __init__(self, destination: str) -> None:
        self.destination = destination

    def send(self, product: Product, snapshot: Snapshot, changes: list[DetectedChange]) -> None:
        settings = get_settings()
        if not settings.resend_api_key:
            logger.error(
                "RESEND_API_KEY is not set; skipping email notification for user_id=%s destination=%s",
                product.user_id,
                self.destination,
            )
            return
        if not settings.resend_from_email:
            logger.error(
                "RESEND_FROM_EMAIL is not set; skipping email notification for user_id=%s destination=%s",
                product.user_id,
                self.destination,
            )
            return

        payload = {
            "from": settings.resend_from_email,
            "to": [self.destination],
            "subject": format_subject(product, changes),
            "text": format_plain_text(product, snapshot, changes),
            "html": format_html(product, snapshot, changes),
        }
        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                RESEND_API_URL,
                json=payload,
                headers=headers,
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            logger.info(
                "Sent email notification to %s for user_id=%s product_id=%s",
                self.destination,
                product.user_id,
                product.id,
            )
        except requests.RequestException as exc:
            logger.error(
                "Failed to send email notification to %s for user_id=%s product_id=%s: %s",
                self.destination,
                product.user_id,
                product.id,
                exc,
            )
