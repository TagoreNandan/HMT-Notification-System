import { DiscoveredProduct } from "../types";

export class HMTStoreSource {
  static source_name = "hmt_store";

  static HEADERS = {
    Origin: "https://www.hmtwatches.store",
    Referer: "https://www.hmtwatches.store/",
    "Content-Type": "application/json",
    "User-Agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  };

  async discover(): Promise<DiscoveredProduct[]> {
    const products: DiscoveredProduct[] = [];

    try {
      // 1. Get all collections
      const resCollections = await fetch(
        "https://api.smartbiz.in/stores/48236/collections?pageSize=20",
        { headers: HMTStoreSource.HEADERS }
      );

      if (!resCollections.ok) {
        throw new Error(`Failed to fetch collections: HTTP ${resCollections.status}`);
      }

      const collectionsData: any = await resCollections.json();
      const collections = collectionsData.collectionEntities || [];

      // Process collections in parallel chunks of 4 to stay under Worker subrequest bounds
      const chunkSize = 4;
      for (let i = 0; i < collections.length; i += chunkSize) {
        const chunk = collections.slice(i, i + chunkSize);
        await Promise.all(
          chunk.map(async (collection: any) => {
            const collectionId = collection.id;
            const collectionName = (collection.name || "").trim();

            try {
              // Get SKUs in this collection
              const resItems = await fetch(
                `https://api.smartbiz.in/stores/48236/collections/${collectionId}/items`,
                { headers: HMTStoreSource.HEADERS }
              );

              if (!resItems.ok) return;

              const itemsData: any = await resItems.json();
              const items = itemsData.collectionItems || [];
              const skus: string[] = items.map((it: any) => it.sku).filter(Boolean);

              if (skus.length === 0) return;

              // Batch fetch product details from smartpos API
              const resProducts = await fetch(
                "https://smartpos.amazon.in/api-unauthenticated/resources/external/catalog/products?groupVariants=true",
                {
                  method: "POST",
                  headers: HMTStoreSource.HEADERS,
                  body: JSON.stringify({
                    filter: { skus },
                    shopId: 48236,
                    offset: 0,
                    limit: 100,
                  }),
                }
              );

              if (!resProducts.ok) return;

              const data: any[] = await resProducts.json();

              for (const item of data) {
                const variants = item.variantsDimensions;
                if (variants && Array.isArray(variants) && variants.length > 0) {
                  for (const variant of variants) {
                    let color = variant.value || "";
                    if (color.includes("_")) {
                      color = color.split("_", 2)[1];
                      color = color.charAt(0).toUpperCase() + color.slice(1);
                    }

                    const title = `${item.name} - ${color}`;
                    const sku = variant.sku || item.sku;
                    const imageUrl =
                      variant.imageUrls && variant.imageUrls.length > 0
                        ? variant.imageUrls[0]
                        : item.productImageUrl || null;

                    products.push({
                      source: "hmt_store",
                      source_product_id: sku,
                      title: title,
                      normalized_title: title.toLowerCase(),
                      url: `https://www.hmtwatches.store/product/${sku}`,
                      collection: collectionName,
                      image_url: imageUrl,
                      price: typeof variant.sellingPrice === "number" ? variant.sellingPrice : null,
                      in_stock: Boolean(variant.inStock),
                    });
                  }
                } else {
                  const sku = item.sku;
                  const title = item.name || "HMT Watch";
                  const inStock =
                    item.buyingOptions?.singlePurchase?.availability?.inStock ?? false;

                  products.push({
                    source: "hmt_store",
                    source_product_id: sku,
                    title: title,
                    normalized_title: title.toLowerCase(),
                    url: `https://www.hmtwatches.store/product/${sku}`,
                    collection: collectionName,
                    image_url: item.productImageUrl || null,
                    price: typeof item.sellingPrice === "number" ? item.sellingPrice : null,
                    in_stock: Boolean(inStock),
                  });
                }
              }
            } catch (colErr) {
              console.warn(`Error processing collection ${collectionId}:`, colErr);
            }
          })
        );
      }
    } catch (err) {
      console.warn("HMTStoreSource discovery failed:", err);
    }

    return products;
  }
}
