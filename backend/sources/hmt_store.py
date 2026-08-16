import httpx

from backend.discovery.models import DiscoveredProduct
from backend.sources.base import BaseSource


class HMTStoreSource(BaseSource):
    source_name = "hmt_store"

    async def discover(self):
        headers = {
            "Origin": "https://www.hmtwatches.store",
            "Referer": "https://www.hmtwatches.store/",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            headers=headers,
            timeout=30,
        ) as client:
            # Get all collections
            response = await client.get(
                "https://api.smartbiz.in/stores/48236/collections?pageSize=20"
            )
            response.raise_for_status()

            collections = response.json()["collectionEntities"]

            products = []

            for collection in collections:
                collection_id = collection["id"]
                collection_name = collection["name"].strip()

                print(f"Fetching {collection_name}...")

                # Get all SKUs in this collection
                response = await client.get(
                    f"https://api.smartbiz.in/stores/48236/collections/{collection_id}/items"
                )
                response.raise_for_status()

                items = response.json()["collectionItems"]
                skus = [item["sku"] for item in items]

                if not skus:
                    continue

                # Fetch product details for those SKUs
                response = await client.post(
                    "https://smartpos.amazon.in/api-unauthenticated/resources/external/catalog/products?groupVariants=true",
                    json={
                        "filter": {
                            "skus": skus,
                        },
                        "shopId": 48236,
                        "offset": 0,
                        "limit": 100,
                    },
                )
                response.raise_for_status()

                data = response.json()

                for item in data:
                    variants = item.get("variantsDimensions")

                    if variants:
                        for variant in variants:
                            color = variant.get("value", "")

                            if "_" in color:
                                color = color.split("_", 1)[1].title()

                            products.append(
                                DiscoveredProduct(
                                    source="hmt_store",
                                    source_product_id=variant["sku"],
                                    title=f"{item['name']} - {color}",
                                    normalized_title=f"{item['name']} - {color}".lower(),
                                    url=f"https://www.hmtwatches.store/product/{variant['sku']}",
                                    collection=collection_name,
                                    image_url=(variant.get("imageUrls") or [None])[0],
                                    price=variant.get("sellingPrice"),
                                    in_stock=variant.get("inStock", False),
                                )
                            )

                    else:
                        products.append(
                            DiscoveredProduct(
                                source="hmt_store",
                                source_product_id=item["sku"],
                                title=item["name"],
                                normalized_title=item["name"].lower(),
                                url=f"https://www.hmtwatches.store/product/{item['sku']}",
                                collection=collection_name,
                                image_url=item.get("productImageUrl"),
                                price=item.get("sellingPrice"),
                                in_stock=item["buyingOptions"]["singlePurchase"][
                                    "availability"
                                ]["inStock"],
                            )
                        )

        print(f"Products found: {len(products)}")
        return products
