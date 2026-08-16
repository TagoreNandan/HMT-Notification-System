from abc import ABC, abstractmethod

from backend.discovery.models import DiscoveredProduct


class BaseSource(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source."""
        ...

    @abstractmethod
    async def discover(self) -> list[DiscoveredProduct]:
        """Discover every product from this source."""
        ...
