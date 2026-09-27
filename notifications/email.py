import logging
from typing import Any

import requests

from config import get_settings
from notifications.base import NotificationChannel
from notifications.messages import (
    format_html,
    format_plain_text,
    format_subject,
)

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailNotificationChannel(NotificationChannel):
    def __init__(self, destination: str) -> None:
        self.destination = destination

    def send(
        self,
        event_or_product: Any,
        snapshot: Any = None,
        changes: Any = None,
    ) -> None:
        settings = get_settings()
        if not settings.resend_api_key:
            logger.error(
                "RESEND_API_KEY is not set; skipping email notification for destination=%s",
                self.destination,
            )
            return
        if not settings.resend_from_email:
            logger.error(
                "RESEND_FROM_EMAIL is not set; skipping email notification for destination=%s",
                self.destination,
            )
            return

        payload = {
            "from": settings.resend_from_email,
            "to": [self.destination],
            "subject": format_subject(event_or_product, changes),
            "text": format_plain_text(event_or_product, snapshot, changes),
            "html": format_html(event_or_product, snapshot, changes),
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
                "Sent email notification to %s",
                self.destination,
            )
        except requests.RequestException as exc:
            logger.error(
                "Failed to send email notification to %s: %s",
                self.destination,
                exc,
            )
