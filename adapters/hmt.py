import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from adapters.base import ProductSnapshot, SiteAdapter


class HMTAdapter(SiteAdapter):
    PRODUCT_PATH = "/product_overview"

    @property
    def site_name(self) -> str:
        return "hmt"

    @staticmethod
    def is_supported_url(url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.netloc.endswith("hmtwatches.in"):
            return False
        return parsed.path.rstrip("/") == HMTAdapter.PRODUCT_PATH and bool(parsed.query)

    def fetch_product(self, url: str):
        raise NotImplementedError(
            "CatalogService should fetch the HTML using Playwright and call parse_html()."
        )

    def parse_html(self, url: str, html: str) -> ProductSnapshot:
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("h3.product-title")
        title = title_el.get_text(strip=True) if title_el else "Unknown Product"

        price = self._parse_price(soup)
        in_stock, stock_raw = self._parse_stock(soup, html)

        description_el = soup.select_one("p.product-description")
        description = description_el.get_text(strip=True) if description_el else None

        return ProductSnapshot(
            url=url,
            title=title,
            price=price,
            in_stock=in_stock,
            raw={
                "description": description,
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
