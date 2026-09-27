import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from adapters.base import ProductSnapshot
from adapters.registry import get_adapter_for_url
from catalog.sync import CatalogSyncService
from core.change_detection import ChangeType, create_notification_event, detect_changes
from db.models import CatalogProduct, ChangeEvent, Product, Snapshot, User
from events.models import NotificationEvent
from notifications.dispatcher import dispatch_event

logger = logging.getLogger(__name__)


class PollingPipeline:
    """
    Structured 5-phase polling pipeline for HMT watch monitoring.

    Phases:
      1. Sync catalog: Synchronize catalog across all HMT sources.
      2. Discover products: Discover active products from both HMT websites.
      3. Detect changes: Compare current state against previous snapshots.
      4. Generate events: Create NotificationEvents for all detected changes.
      5. Dispatch notifications: Dispatch events via channel-agnostic, idempotent dispatcher.
    """

    def __init__(self, db: Session):
        self.db = db
        self.catalog_sync = CatalogSyncService()

    def run(self) -> dict[str, Any]:
        """Execute all 5 phases of the polling pipeline."""
        logger.info("==================================================")
        logger.info("=== STARTING POLLING PIPELINE CYCLE ===")
        logger.info("==================================================")

        # 1. Sync catalog
        catalog_stats = self.phase_1_sync_catalog()

        # 2. Discover products
        discovered_pairs = self.phase_2_discover_products()

        # 3. Detect changes
        change_results = self.phase_3_detect_changes(discovered_pairs)

        # 4. Generate events
        event_pairs = self.phase_4_generate_events(change_results)

        # 5. Dispatch notifications
        dispatch_stats = self.phase_5_dispatch_notifications(event_pairs)

        logger.info("==================================================")
        logger.info(
            "=== PIPELINE CYCLE COMPLETE | Discovered: %d | Changes: %d | Events: %d | Dispatched: %s ===",
            len(discovered_pairs),
            len(change_results),
            len(event_pairs),
            dispatch_stats,
        )
        logger.info("==================================================")

        return {
            "catalog_sync": catalog_stats,
            "discovered_count": len(discovered_pairs),
            "changes_count": len(change_results),
            "events_count": len(event_pairs),
            "dispatch_stats": dispatch_stats,
        }

    def phase_1_sync_catalog(self) -> dict[str, int]:
        logger.info(
            "[PHASE 1/5: SYNC CATALOG] Syncing catalog products across all HMT sources..."
        )
        try:
            stats = self.catalog_sync.sync(self.db)
            logger.info(
                "[PHASE 1/5: SYNC CATALOG] Sync complete | New: %d, Updated: %d, Unchanged: %d",
                stats.get("new", 0),
                stats.get("updated", 0),
                stats.get("unchanged", 0),
            )
            return stats
        except Exception:
            logger.exception("[PHASE 1/5: SYNC CATALOG] Error during catalog sync")
            return {"new": 0, "updated": 0, "unchanged": 0}

    def phase_2_discover_products(self) -> list[tuple[Product, ProductSnapshot]]:
        logger.info(
            "[PHASE 2/5: DISCOVER PRODUCTS] Discovering active products across both HMT websites..."
        )
        # Ensure all discovered CatalogProducts have active Product records if Product table is empty
        products_count = self.db.query(Product).filter(Product.is_active.is_(True)).count()
        if products_count == 0:
            users = self.db.query(User).all()
            catalog_products = self.db.query(CatalogProduct).all()

            if users and catalog_products:
                for cat in catalog_products:
                    for u in users:
                        self.db.add(
                            Product(
                                user_id=u.id,
                                url=cat.url,
                                site_name=cat.site_name,
                                title=cat.title or "HMT Watch",
                                is_active=True,
                            )
                        )
                self.db.commit()

        seen_urls: set[str] = set()
        discovered_pairs: list[tuple[Product, ProductSnapshot]] = []

        products = self.db.query(Product).filter(Product.is_active.is_(True)).all()

        for product in products:
            if product.url in seen_urls:
                logger.info(
                    "[PHASE 2/5: DISCOVER PRODUCTS] Skipping duplicate product URL: %s",
                    product.url,
                )
                continue

            seen_urls.add(product.url)
            try:
                adapter = get_adapter_for_url(product.url)
                curr_snapshot = adapter.fetch_product(product.url)
                discovered_pairs.append((product, curr_snapshot))
                logger.info(
                    "[PHASE 2/5: DISCOVER PRODUCTS] Discovered product id=%s site=%s url=%s title=%r",
                    product.id,
                    product.site_name,
                    product.url,
                    curr_snapshot.title,
                )
            except Exception:
                logger.exception(
                    "[PHASE 2/5: DISCOVER PRODUCTS] Failed to fetch product id=%s url=%s",
                    product.id,
                    product.url,
                )

        logger.info(
            "[PHASE 2/5: DISCOVER PRODUCTS] Discovery complete | Discovered %d unique active products",
            len(discovered_pairs),
        )
        return discovered_pairs

    def phase_3_detect_changes(
        self, discovered_pairs: list[tuple[Product, ProductSnapshot]]
    ) -> list[tuple[Product, Snapshot, list[Any]]]:
        logger.info(
            "[PHASE 3/5: DETECT CHANGES] Comparing current state for %d products...",
            len(discovered_pairs),
        )
        results = []

        for product, current in discovered_pairs:
            previous_db = (
                self.db.query(Snapshot)
                .filter(Snapshot.product_id == product.id)
                .order_by(Snapshot.fetched_at.desc())
                .first()
            )
            previous = (
                ProductSnapshot(
                    url=product.url,
                    title=previous_db.title,
                    price=previous_db.price,
                    in_stock=previous_db.in_stock,
                    raw=previous_db.raw or {},
                )
                if previous_db
                else None
            )

            snapshot = Snapshot(
                product_id=product.id,
                title=current.title,
                price=current.price,
                in_stock=current.in_stock,
                raw=current.raw,
                fetched_at=datetime.now(timezone.utc),
            )
            self.db.add(snapshot)
            self.db.flush()

            changes = detect_changes(previous, current)
            actionable = [c for c in changes if c.change_type != ChangeType.NO_CHANGE]

            for change in actionable:
                event_rec = ChangeEvent(
                    product_id=product.id,
                    snapshot_id=snapshot.id,
                    change_type=change.change_type.value,
                    old_value=change.old_value,
                    new_value=change.new_value,
                    details=change.details,
                )
                self.db.add(event_rec)

            product.title = current.title
            product.updated_at = datetime.now(timezone.utc)
            self.db.commit()

            if actionable:
                logger.info(
                    "[PHASE 3/5: DETECT CHANGES] Detected %d change(s) for product id=%s title=%r",
                    len(actionable),
                    product.id,
                    product.title,
                )
                results.append((product, snapshot, actionable))
            else:
                logger.info(
                    "[PHASE 3/5: DETECT CHANGES] No changes for product id=%s title=%r",
                    product.id,
                    product.title,
                )

        logger.info(
            "[PHASE 3/5: DETECT CHANGES] Change detection complete | %d products with changes",
            len(results),
        )
        return results

    def phase_4_generate_events(
        self, change_results: list[tuple[Product, Snapshot, list[Any]]]
    ) -> list[tuple[int, NotificationEvent]]:
        logger.info(
            "[PHASE 4/5: GENERATE EVENTS] Generating events for detected changes..."
        )
        events: list[tuple[int, NotificationEvent]] = []

        for product, snapshot, changes in change_results:
            raw = snapshot.raw or {}
            image_url = raw.get("image_url") or raw.get("image")
            collection = raw.get("collection") or raw.get("category")

            for change in changes:
                event = create_notification_event(
                    change=change,
                    product_id=product.id,
                    title=snapshot.title or product.title or "Tracked Product",
                    price=snapshot.price,
                    in_stock=snapshot.in_stock,
                    url=product.url,
                    site_name=product.site_name,
                    occurred_at=snapshot.fetched_at,
                    image_url=image_url,
                    collection=collection,
                    snapshot_id=snapshot.id,
                )
                events.append((product.user_id, event))
                logger.info(
                    "[PHASE 4/5: GENERATE EVENTS] Generated NotificationEvent id=%s type=%s product_id=%s user_id=%s",
                    event.event_id,
                    event.event_type,
                    product.id,
                    product.user_id,
                )

        logger.info(
            "[PHASE 4/5: GENERATE EVENTS] Event generation complete | Generated %d NotificationEvents",
            len(events),
        )
        return events

    def phase_5_dispatch_notifications(
        self, events: list[tuple[int, NotificationEvent]]
    ) -> dict[str, int]:
        logger.info(
            "[PHASE 5/5: DISPATCH NOTIFICATIONS] Dispatching %d notification events...",
            len(events),
        )
        stats = {"sent": 0, "suppressed": 0, "failed": 0}

        for user_id, event in events:
            try:
                dispatched = dispatch_event(self.db, user_id, event)
                if dispatched:
                    stats["sent"] += 1
                    logger.info(
                        "[PHASE 5/5: DISPATCH NOTIFICATIONS] Successfully dispatched event_id=%s user_id=%s",
                        event.event_id,
                        user_id,
                    )
                else:
                    stats["suppressed"] += 1
                    logger.info(
                        "[PHASE 5/5: DISPATCH NOTIFICATIONS] Notification suppressed or unverified for event_id=%s user_id=%s",
                        event.event_id,
                        user_id,
                    )
            except Exception:
                stats["failed"] += 1
                logger.exception(
                    "[PHASE 5/5: DISPATCH NOTIFICATIONS] Failed to dispatch event_id=%s user_id=%s",
                    event.event_id,
                    user_id,
                )

        logger.info(
            "[PHASE 5/5: DISPATCH NOTIFICATIONS] Dispatch complete | Stats: %s", stats
        )
        return stats
