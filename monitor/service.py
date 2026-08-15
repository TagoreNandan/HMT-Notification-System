from sqlalchemy.orm import Session
from playwright.sync_api import sync_playwright

from db.models import CatalogProduct
from catalog.service import CatalogService


from services.watchlist_service import WatchlistService

from services.notification_service import NotificationService


class MonitorService:

    def __init__(self):
        self.catalog = CatalogService()

    def check_all(self, db: Session):

        products = db.query(CatalogProduct).all()

        print(f"Checking {len(products)} products...")

        watchlists = WatchlistService(db)
        notification_service = NotificationService(watchlists)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            page = browser.new_page(
                user_agent=self.catalog.settings.user_agent,
            )

            for product in products:
                print(product.title)
                current = self.catalog.check_product(page, product.url)

                print(f"DEBUG current={current!r}")
                print(f"DEBUG type={type(current)}")
                print(f"DEBUG old={product.in_stock!r}")

                if current == product.in_stock:
                    continue

                product.in_stock = current

                db.commit()

                print(f"current={current!r}, type={type(current)}")
                print(f"product.in_stock={product.in_stock!r}")

                if current:
                    print(f"✅ BACK IN STOCK: {product.title}")

                    print("CALLING notify_back_in_stock()")
                    print("BEFORE CALL")
                    notification_service.notify_back_in_stock(product)
                    print("AFTER CALL")

                else:
                    print(f"❌ OUT OF STOCK: {product.title}")

            browser.close()