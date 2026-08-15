from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from adapters.base import ProductSnapshot


class ChangeType(str, Enum):
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
                change_type=ChangeType.NO_CHANGE,
                details={"reason": "initial_snapshot"},
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
