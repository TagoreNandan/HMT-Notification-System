import logging
from datetime import datetime, timezone
from typing import Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.change_detection import ChangeType, DetectedChange, create_notification_event
from db.models import (
    ChannelType,
    NotificationLog,
    NotificationPreference,
    Product,
    Snapshot,
)
from events.models import NotificationEvent
from notifications.base import NotificationChannel
from notifications.console import ConsoleNotificationChannel
from notifications.email import EmailNotificationChannel
from notifications.ntfy import NtfyNotificationChannel
from notifications.whatsapp import WhatsAppNotificationChannel

logger = logging.getLogger(__name__)

# Channel Registry for channel-agnostic dispatching
_CHANNEL_REGISTRY: dict[ChannelType, Type[NotificationChannel]] = {
    ChannelType.EMAIL: EmailNotificationChannel,
    ChannelType.NTFY: NtfyNotificationChannel,
    ChannelType.WHATSAPP: WhatsAppNotificationChannel,
    ChannelType.CONSOLE: ConsoleNotificationChannel,
}


def register_channel(
    channel_type: ChannelType, channel_class: Type[NotificationChannel]
) -> None:
    """Register or override a channel implementation for a ChannelType."""
    _CHANNEL_REGISTRY[channel_type] = channel_class


def get_channel(preference: NotificationPreference) -> NotificationChannel:
    """Instantiate a channel-agnostic NotificationChannel for a given preference."""
    channel_class = _CHANNEL_REGISTRY.get(preference.channel_type)
    if not channel_class:
        raise ValueError(f"Unsupported channel type: {preference.channel_type}")

    if preference.channel_type in {
        ChannelType.EMAIL,
        ChannelType.NTFY,
        ChannelType.WHATSAPP,
    }:
        if not preference.destination:
            raise ValueError(
                f"{preference.channel_type.value.capitalize()} preference requires a destination"
            )
        return channel_class(preference.destination)

    return channel_class()


def dispatch_event(
    db: Session,
    user_id: int,
    event: NotificationEvent,
) -> bool:
    """
    Channel-agnostic, idempotent event dispatcher.
    Sends a NotificationEvent to all active notification preferences for a user.
    Suppresses duplicate alerts for the same event_id + destination.
    """
    preferences = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .order_by(NotificationPreference.created_at.asc())
        .all()
    )

    if not preferences:
        logger.info(
            "User id=%s has no notification preferences configured; falling back to console",
            user_id,
        )
        ConsoleNotificationChannel().send(event)
        return True

    any_sent = False
    for preference in preferences:
        if preference.channel_type == ChannelType.EMAIL and not preference.is_verified:
            logger.info(
                "Skipping unverified email preference id=%s for user_id=%s destination=%s",
                preference.id,
                user_id,
                preference.destination,
            )
            continue

        # IDEMPOTENCY CHECK
        existing_log = (
            db.query(NotificationLog)
            .filter(
                NotificationLog.event_id == event.event_id,
                NotificationLog.channel_type == preference.channel_type,
                NotificationLog.destination == preference.destination,
                NotificationLog.user_id == user_id,
            )
            .first()
        )
        if existing_log:
            logger.info(
                "Idempotency check: duplicate notification suppressed for event_id=%s user_id=%s channel=%s dest=%s",
                event.event_id,
                user_id,
                preference.channel_type.value,
                preference.destination,
            )
            continue

        try:
            channel = get_channel(preference)
            channel.send(event)

            # Record sent event in idempotency log
            log_entry = NotificationLog(
                event_id=event.event_id,
                user_id=user_id,
                channel_type=preference.channel_type,
                destination=preference.destination,
                sent_at=datetime.now(timezone.utc),
            )
            db.add(log_entry)
            db.commit()
            any_sent = True
        except IntegrityError:
            db.rollback()
            logger.info(
                "Concurrent duplicate notification suppressed for event_id=%s user_id=%s channel=%s dest=%s",
                event.event_id,
                user_id,
                preference.channel_type.value,
                preference.destination,
            )
        except Exception:
            db.rollback()
            logger.exception(
                "Failed to dispatch notification via %s for user_id=%s preference_id=%s",
                preference.channel_type.value,
                user_id,
                preference.id,
            )

    return any_sent


def dispatch_product_changes(
    db: Session,
    product: Product,
    snapshot: Snapshot,
    changes: list[DetectedChange],
) -> None:
    actionable = [
        change for change in changes if change.change_type != ChangeType.NO_CHANGE
    ]

    preferences = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == product.user_id)
        .order_by(NotificationPreference.created_at.asc())
        .all()
    )

    raw = snapshot.raw or {}
    image_url = raw.get("image_url") or raw.get("image")
    collection = raw.get("collection") or raw.get("category")

    if not preferences:
        logger.info(
            "User id=%s has no notification preferences configured; falling back to console",
            product.user_id,
        )
        for change in actionable or changes:
            event = create_notification_event(
                change=change,
                product_id=product.id,
                title=snapshot.title or product.title or "Tracked Product",
                price=snapshot.price,
                in_stock=snapshot.in_stock,
                url=product.url,
                site_name=product.site_name,
                occurred_at=snapshot.fetched_at,
                image_url=image_url,
                collection=collection,
                snapshot_id=snapshot.id,
            )
            ConsoleNotificationChannel().send(event)
        return

    if not actionable:
        return

    for change in actionable:
        event = create_notification_event(
            change=change,
            product_id=product.id,
            title=snapshot.title or product.title or "Tracked Product",
            price=snapshot.price,
            in_stock=snapshot.in_stock,
            url=product.url,
            site_name=product.site_name,
            occurred_at=snapshot.fetched_at,
            image_url=image_url,
            collection=collection,
            snapshot_id=snapshot.id,
        )
        dispatch_event(db, product.user_id, event)
