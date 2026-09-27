import logging
import httpx
from bs4 import BeautifulSoup

from backend.discovery.models import DiscoveredProduct
from backend.sources.base import BaseSource

logger = logging.getLogger(__name__)


class HMTInSource(BaseSource):
    @property
    def source_name(self) -> str:
        return "hmt_in"

    async def discover(self) -> list[DiscoveredProduct]:
        products: list[DiscoveredProduct] = []
        base_url = "https://hmtwatches.in"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=15) as client:
                res = await client.get(f"{base_url}/watches")
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    items = soup.select("a[href*='product_overview']")
                    for item in items:
                        href = item.get("href", "")
                        if href and "id=" in href:
                            full_url = (
                                href
                                if href.startswith("http")
                                else f"{base_url}/{href.lstrip('/')}"
                            )
                            title = item.get_text(strip=True) or "HMT Watch"
                            pid = href.split("id=")[-1]
                            products.append(
                                DiscoveredProduct(
                                    source="hmt_in",
                                    source_product_id=pid,
                                    title=title,
                                    normalized_title=title.lower(),
                                    url=full_url,
                                    collection="HMT Collection",
                                    image_url=None,
                                    price=None,
                                    in_stock=True,
                                )
                            )
        except Exception as exc:
            logger.warning("HMTInSource discovery encountered exception: %s", exc)

        return products
