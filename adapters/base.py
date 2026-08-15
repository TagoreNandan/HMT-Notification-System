from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ProductSnapshot(BaseModel):
    url: str
    title: str
    price: float | None = None
    currency: str = "INR"
    in_stock: bool
    raw: dict[str, Any] = Field(default_factory=dict)


class SiteAdapter(ABC):
    @property
    @abstractmethod
    def site_name(self) -> str:
        ...

    @abstractmethod
    def fetch_product(self, url: str) -> ProductSnapshot:
        ...
