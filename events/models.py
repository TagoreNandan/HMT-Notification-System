from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    NEW_PRODUCT = "NEW_PRODUCT"
    RESTOCKED = "RESTOCKED"
    OUT_OF_STOCK = "OUT_OF_STOCK"
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