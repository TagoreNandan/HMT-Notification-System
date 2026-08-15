import logging

from sqlalchemy.orm import Session

from core.change_detection import ChangeType, DetectedChange
from db.models import ChannelType, NotificationPreference, Product, Snapshot
from notifications.base import NotificationChannel
from notifications.console import ConsoleNotificationChannel
from notifications.email import EmailNotificationChannel
from notifications.ntfy import NtfyNotificationChannel
from notifications.whatsapp import WhatsAppNotificationChannel

logger = logging.getLogger(__name__)


def _channel_for_preference(preference: NotificationPreference) -> NotificationChannel:
    if preference.channel_type == ChannelType.EMAIL:
        if not preference.destination:
            raise ValueError("Email preference requires a destination address")
        return EmailNotificationChannel(preference.destination)
    if preference.channel_type == ChannelType.NTFY:
        if not preference.destination:
            raise ValueError("Ntfy preference requires a topic destination")
        return NtfyNotificationChannel(preference.destination)
    if preference.channel_type == ChannelType.CONSOLE:
        return ConsoleNotificationChannel()
    if preference.channel_type == ChannelType.WHATSAPP:
        if not preference.destination:
            raise ValueError("WhatsApp preference requires a destination phone number")
        return WhatsAppNotificationChannel(preference.destination)
    raise ValueError(f"Unsupported channel type: {preference.channel_type}")


def dispatch_product_changes(
    db: Session,
    product: Product,
    snapshot: Snapshot,
    changes: list[DetectedChange],
) -> None:
    actionable = [change for change in changes if change.change_type != ChangeType.NO_CHANGE]

    preferences = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == product.user_id)
        .order_by(NotificationPreference.created_at.asc())
        .all()
    )

    if not preferences:
        logger.info(
            "User id=%s has no notification preferences configured; falling back to console",
            product.user_id,
        )
        ConsoleNotificationChannel().send(product, snapshot, changes)
        return

    if not actionable:
        return

    for preference in preferences:
        if preference.channel_type == ChannelType.EMAIL and not preference.is_verified:
            logger.info(
                "Skipping unverified email preference id=%s for user_id=%s destination=%s",
                preference.id,
                product.user_id,
                preference.destination,
            )
            continue

        try:
            channel = _channel_for_preference(preference)
            channel.send(product, snapshot, actionable)
        except Exception:
            logger.exception(
                "Failed to dispatch notification via %s for user_id=%s preference_id=%s",
                preference.channel_type.value,
                product.user_id,
                preference.id,
            )
