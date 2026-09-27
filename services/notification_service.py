import logging
from datetime import datetime, timezone

from db.models import CatalogProduct
from events.models import NotificationEvent
from notifications.dispatcher import dispatch_event
from services.watchlist_service import WatchlistService

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, watchlists: WatchlistService):
        self.watchlists = watchlists

    def notify_back_in_stock(self, product: CatalogProduct) -> None:
        matching_users = self.watchlists.get_matching_users(product.id)
        if not matching_users:
            logger.info(
                "No users watching catalog product id=%s title=%s",
                product.id,
                product.title,
            )
            return

        ts = product.last_seen or datetime.now(timezone.utc)
        event_id = f"evt_cat_{product.id}_{int(ts.timestamp())}_back_in_stock"

        event = NotificationEvent(
            event_id=event_id,
            event_type="back_in_stock",
            product_id=product.id,
            title=product.title or "HMT Watch",
            price=product.price,
            in_stock=True,
            url=product.url,
            site_name=product.site_name,
            occurred_at=ts,
            old_value="out_of_stock",
            new_value="in_stock",
        )

        for user in matching_users:
            dispatch_event(self.watchlists.db, user.id, event)
