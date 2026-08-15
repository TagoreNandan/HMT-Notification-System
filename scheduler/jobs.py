import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from adapters.base import ProductSnapshot
from adapters.registry import get_adapter_for_url
from core.change_detection import ChangeType, detect_changes
from db.models import ChangeEvent, Product, Snapshot
from notifications.dispatcher import dispatch_product_changes

logger = logging.getLogger(__name__)


def _snapshot_to_product_snapshot(snapshot: Snapshot, url: str) -> ProductSnapshot:
    return ProductSnapshot(
        url=url,
        title=snapshot.title,
        price=snapshot.price,
        in_stock=snapshot.in_stock,
        raw=snapshot.raw or {},
    )


def poll_product(db: Session, product: Product) -> Snapshot:
    adapter = get_adapter_for_url(product.url)
    current = adapter.fetch_product(product.url)

    previous_db = (
        db.query(Snapshot)
        .filter(Snapshot.product_id == product.id)
        .order_by(Snapshot.fetched_at.desc())
        .first()
    )
    previous = (
        _snapshot_to_product_snapshot(previous_db, product.url) if previous_db else None
    )

    snapshot = Snapshot(
        product_id=product.id,
        title=current.title,
        price=current.price,
        in_stock=current.in_stock,
        raw=current.raw,
        fetched_at=datetime.now(timezone.utc),
    )
    db.add(snapshot)
    db.flush()

    changes = detect_changes(previous, current)

    for change in changes:
        if change.change_type == ChangeType.NO_CHANGE:
            continue
        event = ChangeEvent(
            product_id=product.id,
            snapshot_id=snapshot.id,
            change_type=change.change_type.value,
            old_value=change.old_value,
            new_value=change.new_value,
            details=change.details,
        )
        db.add(event)

    product.title = current.title
    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(snapshot)

    dispatch_product_changes(db, product, snapshot, changes)
    return snapshot


def poll_all_products(db: Session) -> int:
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    polled = 0
    for product in products:
        try:
            poll_product(db, product)
            polled += 1
        except Exception:
            logger.exception("Failed to poll product id=%s url=%s", product.id, product.url)
            db.rollback()
    return polled
