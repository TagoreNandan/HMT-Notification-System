from __future__ import annotations

import asyncio
from sqlalchemy.orm import Session

from backend.discovery.discovery_service import DiscoveryService
from backend.discovery.registry import get_sources
from config import get_settings
from db.models import Product


class CatalogService:
    """
    Discovers all products currently available on the HMT website.
    """

    BASE_URL = "https://hmtwatches.in"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.discovery = DiscoveryService(get_sources())

    def fetch_catalog(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    lambda: asyncio.run(self.discovery.discover())
                ).result()
        else:
            return asyncio.run(self.discovery.discover())

    def sync_catalog(self, db: Session) -> int:
        """Discover every watch currently listed by HMT.
        Any newly discovered watch is automatically added to the database and polled immediately.
        Returns the number of newly added watches.
        """
        from scheduler.jobs import poll_product

        snapshots = self.fetch_catalog()
        added = 0

        for snapshot in snapshots:
            existing = (
                db.query(Product).filter(Product.url == snapshot.url).one_or_none()
            )

            if existing:
                continue

            product = Product(
                user_id=0,
                url=snapshot.url,
                site_name="HMT",
                title=snapshot.title,
                is_active=True,
            )

            db.add(product)
            db.commit()
            db.refresh(product)

            poll_product(db, product)

            added += 1

            print(f"Added {snapshot.url}")

        return added
