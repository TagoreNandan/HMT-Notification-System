import asyncio

from backend.discovery.discovery_service import DiscoveryService
from backend.discovery.registry import get_sources


async def main():
    service = DiscoveryService(get_sources())

    products = await service.discover()

    print(f"\nDiscovered {len(products)} products")


if __name__ == "__main__":
    asyncio.run(main())