class DiscoveryService:
    def __init__(self, scrapers):
        self.scrapers = scrapers

    async def discover(self):
        products = []

        for scraper in self.scrapers:
            print(f"Running {scraper.source_name}...")

            discovered = await scraper.discover()

            products.extend(discovered)

        return products