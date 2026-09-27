from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    NEW_MODEL = "new_model"
    NEW_PRODUCT = "NEW_PRODUCT"
    RESTOCKED = "RESTOCKED"
    BACK_IN_STOCK = "back_in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PRICE_CHANGE = "price_change"
    PRICE_INCREASED = "PRICE_INCREASED"
    PRICE_DECREASED = "PRICE_DECREASED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"


@dataclass(slots=True)
class Event:
    event_type: EventType
    product_id: str
    product_name: str
    product_url: str
    occurred_at: datetime
    payload: dict[str, Any]


@dataclass
class NotificationEvent:
    event_id: str
    event_type: str  # "new_model", "back_in_stock", "out_of_stock", "price_change"
    product_id: int | str
    title: str
    price: float | None
    in_stock: bool
    url: str
    site_name: str
    occurred_at: datetime
    image_url: str | None = None
    collection: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    details: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.details is None:
            object.__setattr__(self, "details", {})
