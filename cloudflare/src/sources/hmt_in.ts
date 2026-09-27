import { DiscoveredProduct, ProductSnapshot } from "../types";

export class HMTInSource {
  static BASE_URL = "https://hmtwatches.in";
  static HEADERS = {
    "User-Agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  };

  async discover(): Promise<DiscoveredProduct[]> {
    const products: DiscoveredProduct[] = [];
    try {
      const res = await fetch(`${HMTInSource.BASE_URL}/watches`, {
        headers: HMTInSource.HEADERS,
      });

      if (res.status === 200) {
        const html = await res.text();
        const matches = html.matchAll(/<a\s+[^>]*href=["']([^"']*product_overview[^"']*)["'][^>]*>(.*?)<\/a>/gis);

        const seenUrls = new Set<string>();

        for (const match of matches) {
          const href = match[1];
          const innerHtml = match[2];
          const title = innerHtml.replace(/<[^>]+>/g, "").trim() || "HMT Watch";

          if (href && href.includes("id=")) {
            const fullUrl = href.startsWith("http")
              ? href
              : `${HMTInSource.BASE_URL}/${href.replace(/^\//, "")}`;

            if (seenUrls.has(fullUrl)) continue;
            seenUrls.add(fullUrl);

            const pid = href.split("id=").pop() || fullUrl;

            products.push({
              source: "hmt_in",
              source_product_id: pid,
              title: title,
              normalized_title: title.toLowerCase(),
              url: fullUrl,
              collection: "HMT Collection",
              image_url: null,
              price: null,
              in_stock: true,
            });
          }
        }
      }
    } catch (err) {
      console.warn("HMTInSource discovery failed:", err);
    }
    return products;
  }

  async fetchProduct(url: string): Promise<ProductSnapshot> {
    try {
      const res = await fetch(url, { headers: HMTInSource.HEADERS });
      if (res.status === 200) {
        const html = await res.text();
        return this.parseHtml(url, html);
      }
    } catch (err) {
      console.warn(`HMTInSource fetch failed for ${url}:`, err);
    }

    return {
      url,
      title: "HMT Watch",
      price: null,
      in_stock: true,
      raw: {},
    };
  }

  parseHtml(url: string, html: string): ProductSnapshot {
    // 1. Title: <h3 class="product-title">...</h3>
    let title = "Unknown Product";
    const titleMatch = html.match(/<h3\s+class=["'][^"']*product-title[^"']*["'][^>]*>(.*?)<\/h3>/is);
    if (titleMatch) {
      title = titleMatch[1].replace(/<[^>]+>/g, "").trim() || title;
    }

    // 2. Price: <h4 class="price discountPrice">...</h4> or regex match
    let price: number | null = null;
    const priceMatch = html.match(/<h4\s+class=["'][^"']*price[^"']*discountPrice[^"']*["'][^>]*>(.*?)<\/h4>/is) ||
                       html.match(/<h4\s+class=["'][^"']*discountPrice[^"']*["'][^>]*>(.*?)<\/h4>/is);
    if (priceMatch) {
      const text = priceMatch[1].replace(/<[^>]+>/g, "").replace(/,/g, "");
      const numMatch = text.match(/([\d]+(?:\.\d+)?)/);
      if (numMatch) {
        price = parseFloat(numMatch[1]);
      }
    }

    // 3. Stock parsing:
    // cart_input = input#is_add_to_cart
    let isAddToCart: string | null = null;
    const cartMatch = html.match(/<input\s+[^>]*id=["']is_add_to_cart["'][^>]*value=["']([^"']*)["']/i) ||
                      html.match(/<input\s+[^>]*value=["']([^"']*)["'][^>]*id=["']is_add_to_cart["']/i);
    if (cartMatch) {
      isAddToCart = cartMatch[1];
    }

    // prodInStock = "..."
    const prodInStockMatch = html.match(/prodInStock\s*=\s*["'](\w+)["']/i);
    const prodInStock = prodInStockMatch ? prodInStockMatch[1] : null;

    // prodQty = ...
    const prodQtyMatch = html.match(/prodQty\s*=\s*(?:parseInt\()?["']?(\d+)["']?\)?/i);
    const prodQty = prodQtyMatch ? parseInt(prodQtyMatch[1], 10) : null;

    // prodMaxOrdQtry = ...
    const prodMaxMatch = html.match(/prodMaxOrdQtry\s*=\s*(?:parseInt\()?["']?(\d+)["']?\)?/i);
    const prodMax = prodMaxMatch ? parseInt(prodMaxMatch[1], 10) : null;

    let inStock = false;
    if (isAddToCart === "1" || prodInStock === "yes") {
      inStock = true;
    } else if (isAddToCart === "0" || prodInStock === "no") {
      inStock = false;
    } else if (prodQty !== null && prodQty > 0) {
      inStock = true;
    }

    // 4. Image URL:
    let imageUrl: string | null = null;
    const imgMatch = html.match(/<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']/i) ||
                     html.match(/<div\s+class=["'][^"']*(?:img-container|preview-pic)[^"']*["'][^>]*>\s*<img\s+[^>]*src=["']([^"']+)["']/i);
    if (imgMatch) {
      const src = imgMatch[1];
      if (src.startsWith("http")) {
        imageUrl = src;
      } else {
        imageUrl = `${HMTInSource.BASE_URL}/${src.replace(/^\//, "")}`;
      }
    }

    // 5. Collection:
    let collection: string | null = null;
    const colMatch = html.match(/<ol\s+class=["']breadcrumb["'][^>]*>.*?<li>.*?<\/li>\s*<li>(.*?)<\/li>/is);
    if (colMatch) {
      collection = colMatch[1].replace(/<[^>]+>/g, "").trim() || null;
    }

    return {
      url,
      title,
      price,
      in_stock: inStock,
      raw: {
        image_url: imageUrl,
        collection,
        is_add_to_cart: isAddToCart,
        prodInStock,
        prodQty,
        prodMaxOrdQtry: prodMax,
      },
    };
  }
}
