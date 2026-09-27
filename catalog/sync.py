from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from catalog.service import CatalogService
from db.models import CatalogProduct, utcnow

logger = logging.getLogger(__name__)


class CatalogSyncService:
    def __init__(self) -> None:
        self.catalog = CatalogService()

    def sync(self, db: Session) -> dict[str, int]:
        discovered = self.catalog.fetch_catalog()
        seen_urls: set[str] = set()

        stats = {
            "new": 0,
            "updated": 0,
            "unchanged": 0,
        }

        for product in discovered:
            # Skip duplicate watch titles
            if product.url in seen_urls:
                continue

            seen_urls.add(product.url)

            existing = (
                db.query(CatalogProduct)
                .filter(
                    CatalogProduct.site_name == product.source,
                    CatalogProduct.url == product.url,
                )
                .one_or_none()
            )

            if existing is None:
                db.add(
                    CatalogProduct(
                        url=product.url,
                        site_name=product.source,
                        title=product.title,
                        price=float(product.price) if product.price else None,
                        in_stock=product.in_stock,
                    )
                )
                stats["new"] += 1
                continue

            new_price = None
            if product.price is not None:
                try:
                    new_price = float(product.price)
                except (ValueError, TypeError):
                    new_price = None

            changed = False
            existing.last_seen = utcnow()

            if existing.title != product.title and product.title:
                existing.title = product.title
                changed = True

            if existing.price != new_price:
                if (
                    existing.price is None
                    or new_price is None
                    or abs(existing.price - new_price) > 0.001
                ):
                    existing.price = new_price
                    changed = True

            if existing.in_stock != product.in_stock:
                existing.in_stock = product.in_stock
                changed = True

            if changed:
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        db.commit()

        logger.info(
            "Catalog Sync Complete | new=%d updated=%d unchanged=%d",
            stats["new"],
            stats["updated"],
            stats["unchanged"],
        )

        return stats
