from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import CatalogProduct
from db.session import get_db

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("")
def list_catalog(db: Session = Depends(get_db)):
    products = (
        db.query(CatalogProduct)
        .order_by(CatalogProduct.title)
        .all()
    )

    return [
    {
        "id": p.id,
        "title": p.title,
        "url": p.url,
        "in_stock": p.in_stock,
    }
    for p in products
]