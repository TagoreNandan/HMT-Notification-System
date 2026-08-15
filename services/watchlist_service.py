from sqlalchemy.orm import Session, joinedload

from db.models import User, WatchlistItem


class WatchlistService:

    def __init__(self, db: Session):
        self.db = db

    def get_matching_users(self, product_id: int) -> list[User]:
        items = (
            self.db.query(WatchlistItem)
            .filter(
                WatchlistItem.catalog_product_id == product_id
            )
            .options(
                joinedload(WatchlistItem.user)
                .joinedload(User.notification_preferences)
            )
            .all()
        )

        return [item.user for item in items]