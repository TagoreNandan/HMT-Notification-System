import logging
import time
from typing import Any

import requests

from config import get_settings
from notifications.base import NotificationChannel
from notifications.messages import _to_event

logger = logging.getLogger(__name__)


def format_ntfy_message(
    event_or_product: Any,
    snapshot: Any = None,
    changes: Any = None,
) -> tuple[str, str, str]:
    """
    Format concise ntfy notification.
    Returns: (title, body, product_url)
    """
    evt = _to_event(event_or_product, snapshot, changes)

    etype = evt.event_type
    if etype == "new_model":
        emoji = "✨"
        event_label = "New Model"
    elif etype in ("back_in_stock", "restocked", "RESTOCKED"):
        emoji = "✅"
        event_label = "Back in Stock"
    elif etype in ("out_of_stock", "OUT_OF_STOCK"):
        emoji = "❌"
        event_label = "Out of Stock"
    elif etype in ("price_change", "PRICE_CHANGE"):
        emoji = "💰"
        event_label = "Price Change"
    else:
        emoji = "🔔"
        event_label = "Product Alert"

    title = f"{emoji} {event_label} — {evt.title}"

    if isinstance(evt.price, (int, float)):
        price_str = f"₹{evt.price:,.2f}"
    elif evt.price is not None:
        price_str = f"₹{evt.price}"
    else:
        price_str = "N/A"

    stock_str = "In Stock ✅" if evt.in_stock else "Out of Stock ❌"

    lines = [
        f"⌚ {evt.title}",
        f"Price: {price_str}",
        f"Stock: {stock_str}",
    ]

    if evt.old_value is not None or evt.new_value is not None:
        lines.append(f"Change: {evt.old_value} → {evt.new_value}")

    if evt.collection:
        lines.append(f"Collection: {evt.collection}")

    lines.append(f"URL: {evt.url}")

    body = "\n".join(lines)
    return title, body, evt.url


class NtfyNotificationChannel(NotificationChannel):
    def __init__(self, destination: str, server_url: str | None = None) -> None:
        self.destination = destination.strip()
        self._server_url = server_url

    def get_url(self) -> str:
        settings = get_settings()
        base_url = (self._server_url or settings.ntfy_server_url).rstrip("/")
        if self.destination.startswith("http://") or self.destination.startswith(
            "https://"
        ):
            return self.destination
        topic = self.destination.strip("/")
        return f"{base_url}/{topic}"

    def send(
        self,
        event_or_product: Any,
        snapshot: Any = None,
        changes: Any = None,
    ) -> None:
        settings = get_settings()
        url = self.get_url()

        title, body, product_url = format_ntfy_message(
            event_or_product, snapshot, changes
        )

        headers = {
            "Title": title,
            "Click": product_url,
            "Tags": "watch,shopping_cart",
            "Content-Type": "text/plain; charset=utf-8",
        }

        max_retries = max(1, settings.ntfy_max_retries)
        backoff = settings.ntfy_retry_backoff_seconds

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    url,
                    data=body.encode("utf-8"),
                    headers=headers,
                    timeout=settings.request_timeout_seconds,
                )

                if response.status_code in {429, 500, 502, 503, 504}:
                    if attempt < max_retries:
                        logger.warning(
                            "Transient ntfy failure (status %s) for topic %s on attempt %s/%s. Retrying in %ss...",
                            response.status_code,
                            self.destination,
                            attempt,
                            max_retries,
                            backoff * attempt,
                        )
                        time.sleep(backoff * attempt)
                        continue

                response.raise_for_status()
                logger.info(
                    "Sent ntfy notification to topic %s",
                    self.destination,
                )
                return

            except requests.RequestException as exc:
                is_transient = isinstance(
                    exc, (requests.Timeout, requests.ConnectionError)
                ) or (
                    hasattr(exc, "response")
                    and exc.response is not None
                    and exc.response.status_code in {429, 500, 502, 503, 504}
                )

                if is_transient and attempt < max_retries:
                    logger.warning(
                        "Transient ntfy error (%s) for topic %s on attempt %s/%s. Retrying in %ss...",
                        exc,
                        self.destination,
                        attempt,
                        max_retries,
                        backoff * attempt,
                    )
                    time.sleep(backoff * attempt)
                else:
                    logger.error(
                        "Failed to send ntfy notification to topic %s (attempt %s/%s): %s",
                        self.destination,
                        attempt,
                        max_retries,
                        exc,
                    )
                    if not is_transient:
                        break
