from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from adapters.hmt import HMTAdapter
from config import get_settings
from playwright.sync_api import sync_playwright

from sqlalchemy.orm import Session

from db.models import Product
from scheduler.jobs import poll_product



class CatalogService:
    """
    Discovers all products currently available on the HMT website.
    """

    BASE_URL = "https://hmtwatches.in"

    def __init__(self) -> None:
        self.adapter = HMTAdapter()
        self.settings = get_settings()

    def fetch_catalog(self):
        snapshots = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            page = browser.new_page(
                user_agent=self.settings.user_agent,
            )

            page.goto(
                "https://www.hmtwatches.in/collection",
                wait_until="networkidle",
            )

            urls = self._fetch_product_urls(page)

            for url in urls:
                try:
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )

                    html = page.content()

                    snapshot = self.adapter.parse_html(url, html)

                    snapshots.append(snapshot)

                except Exception as e:
                    print(f"Failed {url}: {e}")
                    continue

            browser.close()

        return snapshots


    def check_product(self, page, url: str) -> bool:
        """
        Visit a product page and return True if the watch is in stock,
        otherwise return False.
        """

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        html = page.content()

        # HMT product pages display this text when the watch is unavailable.
        
        in_stock = "Out Of Stock" not in html

        print(f"{url} -> {'IN STOCK' if in_stock else 'OUT OF STOCK'}")

        return in_stock

    def _fetch_product_urls(self, page) -> list[str]:
        urls: set[str] = set()

        page.goto(
            "https://www.hmtwatches.in/collection",
            wait_until="networkidle",
        )

        page.wait_for_timeout(3000)

        # Keep clicking Load More until it disappears
        
        while True:
            try:
                button = page.locator("#loadMoreBtnData")

                if button.count() == 0:
                    break

                if not button.is_visible():
                    break

                print("Loading more...")
                    
                button.click(timeout=3000)

                page.wait_for_timeout(2500)

            except Exception:
                break

        html = page.content()

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/product_overview" in href:
                urls.add(urljoin(self.BASE_URL, href))

        print(f"Discovered {len(urls)} unique products")

        return sorted(urls)

    def sync_catalog(self, db: Session) -> int:
        """Discover every watch currently listed by HMT.
        Any newly discovered watch is automatically added to the database and polled immediately.
        Returns the number of newly added watches.
        """

        snapshots = self.fetch_catalog()
        added = 0

        for snapshot in snapshots:
            existing = (
                db.query(Product)
                .filter(Product.url == snapshot.url)
                .one_or_none()
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