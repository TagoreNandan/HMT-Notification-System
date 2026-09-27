from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from adapters.base import ProductSnapshot
from events.models import NotificationEvent


class ChangeType(str, Enum):
    NEW_MODEL = "new_model"
    PRICE_CHANGE = "price_change"
    BACK_IN_STOCK = "back_in_stock"
    OUT_OF_STOCK = "out_of_stock"
    NO_CHANGE = "no_change"


class DetectedChange(BaseModel):
    change_type: ChangeType
    old_value: str | None = None
    new_value: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


def detect_changes(
    previous: ProductSnapshot | None, current: ProductSnapshot
) -> list[DetectedChange]:
    if previous is None:
        return [
            DetectedChange(
                change_type=ChangeType.NEW_MODEL,
                new_value=current.title,
                details={"reason": "new_model"},
            )
        ]

    changes: list[DetectedChange] = []

    prev_price = previous.price
    curr_price = current.price
    if prev_price != curr_price:
        changes.append(
            DetectedChange(
                change_type=ChangeType.PRICE_CHANGE,
                old_value=str(prev_price) if prev_price is not None else None,
                new_value=str(curr_price) if curr_price is not None else None,
                details={"currency": current.currency},
            )
        )

    if previous.in_stock != current.in_stock:
        if current.in_stock:
            changes.append(
                DetectedChange(
                    change_type=ChangeType.BACK_IN_STOCK,
                    old_value="out_of_stock",
                    new_value="in_stock",
                )
            )
        else:
            changes.append(
                DetectedChange(
                    change_type=ChangeType.OUT_OF_STOCK,
                    old_value="in_stock",
                    new_value="out_of_stock",
                )
            )

    if not changes:
        changes.append(DetectedChange(change_type=ChangeType.NO_CHANGE))

    return changes


def create_notification_event(
    change: DetectedChange,
    product_id: int | str,
    title: str,
    price: float | None,
    in_stock: bool,
    url: str,
    site_name: str,
    occurred_at: datetime | None = None,
    image_url: str | None = None,
    collection: str | None = None,
    snapshot_id: int | str | None = None,
) -> NotificationEvent:
    if occurred_at is None:
        occurred_at = datetime.now(timezone.utc)

    snap_part = f"_snap_{snapshot_id}" if snapshot_id is not None else ""
    event_id = f"evt_p{product_id}{snap_part}_{change.change_type.value}"

    return NotificationEvent(
        event_id=event_id,
        event_type=change.change_type.value,
        product_id=product_id,
        title=title,
        price=price,
        in_stock=in_stock,
        url=url,
        site_name=site_name,
        occurred_at=occurred_at,
        image_url=image_url,
        collection=collection,
        old_value=change.old_value,
        new_value=change.new_value,
        details=change.details,
    )
