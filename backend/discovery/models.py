from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class DiscoveredProduct:
    source: str

    source_product_id: Optional[str]

    title: str

    normalized_title: str

    url: str

    collection: Optional[str]

    image_url: Optional[str]

    price: Optional[str]

    in_stock: bool
