from urllib.parse import urlparse

from adapters.base import SiteAdapter
from adapters.hmt import HMTAdapter


class UnsupportedSiteError(Exception):
    pass


_ADAPTERS: list[type[SiteAdapter]] = [HMTAdapter]


def get_adapter_for_url(url: str) -> SiteAdapter:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain.endswith("hmtwatches.in"):
        adapter = HMTAdapter()
        if not adapter.is_supported_url(url):
            raise UnsupportedSiteError(
                "HMT URLs must be product_overview pages with an id query parameter"
            )
        return adapter

    raise UnsupportedSiteError(f"No adapter registered for domain: {domain}")


def get_adapter_by_site_name(site_name: str) -> SiteAdapter:
    normalized = site_name.lower()
    for adapter_cls in _ADAPTERS:
        adapter = adapter_cls()
        if adapter.site_name == normalized:
            return adapter
    raise UnsupportedSiteError(f"No adapter registered for site: {site_name}")
