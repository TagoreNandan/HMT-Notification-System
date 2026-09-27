import logging
from typing import Any

import requests

from config import get_settings
from notifications.base import NotificationChannel
from notifications.messages import format_whatsapp

logger = logging.getLogger(__name__)


class WhatsAppNotificationChannel(NotificationChannel):
    def __init__(self, destination: str) -> None:
        self.destination = destination

    def _payload(
        self,
        event_or_product: Any,
        snapshot: Any = None,
        changes: Any = None,
    ) -> dict:
        settings = get_settings()

        return {
            "messaging_product": "whatsapp",
            "to": self.destination,
            "type": "template",
            "template": {
                "name": settings.whatsapp_template_name,
                "language": {
                    "code": "en",
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": format_whatsapp(
                                    event_or_product,
                                    snapshot,
                                    changes,
                                ),
                            }
                        ],
                    }
                ],
            },
        }

    def send(
        self,
        event_or_product: Any,
        snapshot: Any = None,
        changes: Any = None,
    ) -> None:
        settings = get_settings()

        if not settings.whatsapp_access_token:
            logger.error("WHATSAPP_ACCESS_TOKEN is not configured")
            return

        if not settings.whatsapp_phone_number_id:
            logger.error("WHATSAPP_PHONE_NUMBER_ID is not configured")
            return

        url = (
            f"https://graph.facebook.com/"
            f"{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )

        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url,
                json=self._payload(event_or_product, snapshot, changes),
                headers=headers,
                timeout=settings.request_timeout_seconds,
            )

            response.raise_for_status()

            logger.info(
                "Sent WhatsApp notification to %s",
                self.destination,
            )

        except requests.RequestException:
            logger.exception(
                "Failed sending WhatsApp notification to %s",
                self.destination,
            )
