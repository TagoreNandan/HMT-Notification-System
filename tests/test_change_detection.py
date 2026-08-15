from adapters.base import ProductSnapshot
from core.change_detection import ChangeType, detect_changes


def test_detect_price_change() -> None:
    previous = ProductSnapshot(
        url="https://example.com/p",
        title="Watch",
        price=1950.0,
        in_stock=True,
    )
    current = ProductSnapshot(
        url="https://example.com/p",
        title="Watch",
        price=2100.0,
        in_stock=True,
    )

    changes = detect_changes(previous, current)
    types = {c.change_type for c in changes}

    assert ChangeType.PRICE_CHANGE in types
    assert ChangeType.NO_CHANGE not in types


def test_detect_back_in_stock() -> None:
    previous = ProductSnapshot(
        url="https://example.com/p",
        title="Watch",
        price=1950.0,
        in_stock=False,
    )
    current = ProductSnapshot(
        url="https://example.com/p",
        title="Watch",
        price=1950.0,
        in_stock=True,
    )

    changes = detect_changes(previous, current)
    types = {c.change_type for c in changes}

    assert ChangeType.BACK_IN_STOCK in types


def test_detect_out_of_stock() -> None:
    previous = ProductSnapshot(
        url="https://example.com/p",
        title="Watch",
        price=1950.0,
        in_stock=True,
    )
    current = ProductSnapshot(
        url="https://example.com/p",
        title="Watch",
        price=1950.0,
        in_stock=False,
    )

    changes = detect_changes(previous, current)
    types = {c.change_type for c in changes}

    assert ChangeType.OUT_OF_STOCK in types


def test_detect_no_change() -> None:
    snapshot = ProductSnapshot(
        url="https://example.com/p",
        title="Watch",
        price=1950.0,
        in_stock=True,
    )

    changes = detect_changes(snapshot, snapshot)
    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.NO_CHANGE
