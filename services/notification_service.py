from db.models import ChannelType, CatalogProduct, NotificationPreference
from notifications.hmt_email import HMTEmailNotifier
from services.watchlist_service import WatchlistService


print("LOADED notification_service.py")


class NotificationService:
    def __init__(self, watchlists: WatchlistService):
        self.watchlists = watchlists

    def notify_back_in_stock(self, product: CatalogProduct) -> None:
        print(f"DEBUG product = {product.title}")
        matching_users = self.watchlists.get_matching_users(product.id)

        print(f"DEBUG matches = {[u.email for u in matching_users]}")

        if not matching_users:
            print(f"⏭️ No users watching: {product.title}")
            return

        for user in matching_users:
            print(f"⭐ Watchlist match for {user.email}")
            print(f"DEBUG preferences={len(user.notification_preferences)}")

            for preference in user.notification_preferences:
                print(
                    f"DEBUG channel={preference.channel_type} "
                    f"verified={preference.is_verified} "
                    f"dest={preference.destination}"
                )

                if not preference.is_verified:
                    continue

                self._send_notification(
                    preference=preference,
                    product=product,
                )

                print("ENTERED notify_back_in_stock")

    def _send_notification(
        self,
        preference: NotificationPreference,
        product: CatalogProduct,
    ) -> None:

        if preference.channel_type == ChannelType.EMAIL:
            HMTEmailNotifier(preference.destination).send(product)

        # We'll add these next
        elif preference.channel_type == ChannelType.NTFY:
            pass

        elif preference.channel_type == ChannelType.WHATSAPP:
            pass

        elif preference.channel_type == ChannelType.CONSOLE:
            pass
