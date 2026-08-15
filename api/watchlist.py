from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import WatchlistItem, CatalogProduct
from db.session import get_db
from datetime import datetime, timezone

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


USER_ID = 7      # temporary until auth is connected


@router.get("")
def my_watchlist(db: Session = Depends(get_db)):
    rows = (
        db.query(CatalogProduct)
        .join(
            WatchlistItem,
            WatchlistItem.catalog_product_id == CatalogProduct.id,
        )
        .filter(WatchlistItem.user_id == USER_ID)
        .all()
    )

    return [
        {
            "id": p.id,
            "title": p.title,
            "in_stock": p.in_stock,
        }
        for p in rows
    ]

@router.post("/{catalog_product_id}")
def add_watch(
    catalog_product_id: int,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == USER_ID,
            WatchlistItem.catalog_product_id == catalog_product_id,
        )
        .first()
    )

    if existing:
        return {"message": "Already watching"}

    item = WatchlistItem(
        user_id=USER_ID,
        catalog_product_id=catalog_product_id,
        created_at=datetime.now(timezone.utc),
    )

    db.add(item)
    db.commit()

    return {"message": "Added"}


@router.delete("/{catalog_product_id}")
def remove_watch(
    catalog_product_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == USER_ID,
            WatchlistItem.catalog_product_id == catalog_product_id,
        )
        .first()
    )

    if not item:
        return {"message": "Not found"}

    db.delete(item)
    db.commit()

    return {"message": "Removed"}

