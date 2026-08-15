from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from adapters.registry import UnsupportedSiteError, get_adapter_for_url
from api.deps import get_current_user, get_db
from config import get_settings
from db.models import ChangeEvent, Product, Snapshot, User
from scheduler.jobs import poll_product
from services.product_service import ProductService

router = APIRouter()


class ProductCreateRequest(BaseModel):
    url: HttpUrl


class ProductResponse(BaseModel):
    id: int
    url: str
    site_name: str
    title: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SnapshotResponse(BaseModel):
    id: int
    product_id: int
    title: str
    price: float | None
    in_stock: bool
    raw: dict
    fetched_at: datetime

    model_config = {"from_attributes": True}


class ChangeEventResponse(BaseModel):
    id: int
    product_id: int
    snapshot_id: int
    change_type: str
    old_value: str | None
    new_value: str | None
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductHistoryResponse(BaseModel):
    product: ProductResponse
    snapshots: list[SnapshotResponse]
    change_events: list[ChangeEventResponse]


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str



@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    from config import get_settings

    return HealthResponse(app=get_settings().app_name)


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Product:
    url = str(payload.url)

    try:
        adapter = get_adapter_for_url(url)
    except UnsupportedSiteError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    existing = (
        db.query(Product)
        .filter(Product.url == url, Product.user_id == current_user.id)
        .one_or_none()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product URL is already tracked",
        )

    settings = get_settings()
    product_count = (
        db.query(Product).filter(Product.user_id == current_user.id).count()
    )
    if product_count >= settings.max_products_per_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Product limit reached ({settings.max_products_per_user} max). "
                "Delete a tracked product before adding another."
            ),
        )

    snapshot_data = adapter.fetch_product(url)

    product = Product(
        user_id=current_user.id,
        url=url,
        site_name=adapter.site_name,
        title=snapshot_data.title,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    poll_product(db, product)
    db.refresh(product)
    return product


@router.get("/products", response_model=list[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Product]:
    return (
        db.query(Product)
        .filter(Product.user_id == current_user.id)
        .order_by(Product.created_at.desc())
        .all()
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = ProductService(db)

    product = service.get_user_product(
        product_id=product_id,
        user_id=current_user.id,
    )

    if product is None:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Product not found",
    )
    db.delete(product)
    db.commit()


@router.get("/products/{product_id}/history", response_model=ProductHistoryResponse)
def product_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductHistoryResponse:

    service = ProductService(db)

    product = service.get_user_product(
        product_id=product_id,
        user_id=current_user.id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.product_id == product_id)
        .order_by(Snapshot.fetched_at.desc())
        .all()
    )
    change_events = (
        db.query(ChangeEvent)
        .filter(ChangeEvent.product_id == product_id)
        .order_by(ChangeEvent.created_at.desc())
        .all()
    )

    return ProductHistoryResponse(
        product=ProductResponse.model_validate(product),
        snapshots=[SnapshotResponse.model_validate(s) for s in snapshots],
        change_events=[ChangeEventResponse.model_validate(e) for e in change_events],
    )


@router.post("/products/{product_id}/refresh")
def refresh_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductService(db)

    product = service.get_user_product(
        product_id=product_id,
        user_id=current_user.id,
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    snapshot = poll_product(db, product)

    return {
        "message": "Product refreshed",
        "price": snapshot.price,
        "in_stock": snapshot.in_stock,
    }