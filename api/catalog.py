from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from catalog.sync import CatalogSyncService
from db.models import CatalogProduct, Snapshot
from db.session import get_db

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("")
def list_catalog(db: Session = Depends(get_db)):
    products = db.query(CatalogProduct).order_by(CatalogProduct.title).all()

    return [
        {
            "id": p.id,
            "title": p.title,
            "url": p.url,
            "in_stock": p.in_stock,
            "price": p.price,
            "site_name": p.site_name,
            "last_seen": p.last_seen.isoformat() if p.last_seen else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]


@router.get("/status")
def catalog_status(db: Session = Depends(get_db)):
    total = db.query(func.count(CatalogProduct.id)).scalar() or 0
    in_stock = (
        db.query(func.count(CatalogProduct.id))
        .filter(CatalogProduct.in_stock.is_(True))
        .scalar()
        or 0
    )
    out_of_stock = total - in_stock

    latest_catalog_seen = db.query(func.max(CatalogProduct.last_seen)).scalar()
    latest_snapshot_fetched = db.query(func.max(Snapshot.fetched_at)).scalar()

    last_poll = (
        latest_snapshot_fetched or latest_catalog_seen or datetime.now(timezone.utc)
    )
    last_sync = latest_catalog_seen or datetime.now(timezone.utc)

    # Next poll interval is 15 minutes (900 seconds)
    poll_interval = 900
    elapsed_seconds = int(
        (
            datetime.now(timezone.utc)
            - (
                last_poll
                if last_poll.tzinfo
                else last_poll.replace(tzinfo=timezone.utc)
            )
        ).total_seconds()
    )
    next_poll_in = max(0, poll_interval - (elapsed_seconds % poll_interval))

    return {
        "total_watches": total,
        "in_stock": in_stock,
        "out_of_stock": out_of_stock,
        "last_catalog_sync": last_sync.isoformat() if last_sync else None,
        "last_poll": last_poll.isoformat() if last_poll else None,
        "next_poll_seconds": next_poll_in,
        "is_monitoring": True,
    }


@router.post("/sync")
def sync_catalog(db: Session = Depends(get_db)):
    service = CatalogSyncService()
    stats = service.sync(db)
    return {
        "message": "Catalog sync complete",
        "stats": stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
