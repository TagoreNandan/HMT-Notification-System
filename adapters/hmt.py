import logging
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from adapters.base import ProductSnapshot, SiteAdapter

logger = logging.getLogger(__name__)


class HMTAdapter(SiteAdapter):
    PRODUCT_PATH = "/product_overview"

    @property
    def site_name(self) -> str:
        return "hmt"

    @staticmethod
    def is_supported_url(url: str) -> bool:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.endswith("hmtwatches.in"):
            return parsed.path.rstrip("/") == HMTAdapter.PRODUCT_PATH and bool(
                parsed.query
            )
        if netloc.endswith("hmtwatches.store"):
            return "/product" in parsed.path or bool(parsed.path)
        return False

    def fetch_product(self, url: str) -> ProductSnapshot:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.text:
                return self.parse_html(url, resp.text)
        except Exception as exc:
            logger.warning("HTTP fetch failed for url %s: %s", url, exc)

        return ProductSnapshot(
            url=url,
            title="HMT Watch",
            price=None,
            in_stock=True,
            raw={},
        )

    def parse_html(self, url: str, html: str) -> ProductSnapshot:
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("h3.product-title")
        title = title_el.get_text(strip=True) if title_el else "Unknown Product"

        price = self._parse_price(soup)
        in_stock, stock_raw = self._parse_stock(soup, html)

        description_el = soup.select_one("p.product-description")
        description = description_el.get_text(strip=True) if description_el else None

        image_el = soup.select_one(
            "div.img-container img, div.preview-pic img, meta[property='og:image']"
        )
        image_url = None
        if image_el:
            src = image_el.get("src") or image_el.get("content")
            if src:
                if src.startswith("http"):
                    image_url = src
                else:
                    image_url = f"https://hmtwatches.in/{src.lstrip('/')}"

        collection_el = soup.select_one(
            ".breadcrumb li:nth-child(2), .product-collection, .category"
        )
        collection = collection_el.get_text(strip=True) if collection_el else None

        return ProductSnapshot(
            url=url,
            title=title,
            price=price,
            in_stock=in_stock,
            raw={
                "description": description,
                "image_url": image_url,
                "collection": collection,
                **stock_raw,
            },
        )

    @staticmethod
    def _parse_price(soup: BeautifulSoup) -> float | None:
        price_el = soup.select_one("h4.price.discountPrice")
        if not price_el:
            return None

        text = price_el.get_text(" ", strip=True)
        match = re.search(r"([\d,]+(?:\.\d+)?)", text.replace(",", ""))
        if not match:
            return None
        return float(match.group(1))

    @staticmethod
    def _parse_stock(
        soup: BeautifulSoup, html: str
    ) -> tuple[bool, dict[str, str | int | None]]:
        raw: dict[str, str | int | None] = {}

        cart_input = soup.select_one("input#is_add_to_cart")

        is_add_to_cart: str | None = None
        if cart_input:
            value = cart_input.get("value")
            if isinstance(value, str):
                is_add_to_cart = value

        raw["is_add_to_cart"] = is_add_to_cart

        prod_in_stock_match = re.search(r'prodInStock\s*=\s*"(\w+)"', html)
        prod_in_stock = prod_in_stock_match.group(1) if prod_in_stock_match else None
        raw["prodInStock"] = prod_in_stock

        prod_qty_match = re.search(
            r'prodQty\s*=\s*(?:parseInt\()?["\']?(\d+)["\']?\)?', html
        )
        prod_qty = int(prod_qty_match.group(1)) if prod_qty_match else None
        raw["prodQty"] = prod_qty

        prod_max_match = re.search(
            r'prodMaxOrdQtry\s*=\s*(?:parseInt\()?["\']?(\d+)["\']?\)?', html
        )
        prod_max = int(prod_max_match.group(1)) if prod_max_match else None
        raw["prodMaxOrdQtry"] = prod_max

        in_stock = False
        if is_add_to_cart == "1":
            in_stock = True
        elif prod_in_stock == "yes":
            in_stock = True
        elif is_add_to_cart == "0" or prod_in_stock == "no":
            in_stock = False
        elif prod_qty is not None and prod_qty > 0:
            in_stock = True

        return in_stock, raw
