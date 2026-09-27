import { describe, expect, it } from "vitest";
import { HMTInSource } from "../src/sources/hmt_in";

describe("HMTInSource HTML Parser", () => {
  const sampleHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta property="og:image" content="https://hmtwatches.in/uploads/kohinoor.jpg" />
      </head>
      <body>
        <ol class="breadcrumb">
          <li>Home</li>
          <li>Mechanical</li>
        </ol>
        <h3 class="product-title">HMT Kohinoor Yellow Dial Mechanical</h3>
        <h4 class="price discountPrice">₹ 3,200.00</h4>
        <input type="hidden" id="is_add_to_cart" value="1" />
        <script>
          var prodInStock = "yes";
          var prodQty = 5;
        </script>
      </body>
    </html>
  `;

  it("parses title, price, in_stock, image_url, and collection correctly", () => {
    const parser = new HMTInSource();
    const snapshot = parser.parseHtml(
      "https://hmtwatches.in/product_overview?id=789",
      sampleHtml
    );

    expect(snapshot.title).toBe("HMT Kohinoor Yellow Dial Mechanical");
    expect(snapshot.price).toBe(3200);
    expect(snapshot.in_stock).toBe(true);
    expect(snapshot.raw.image_url).toBe("https://hmtwatches.in/uploads/kohinoor.jpg");
    expect(snapshot.raw.collection).toBe("Mechanical");
  });

  it("detects OUT_OF_STOCK when is_add_to_cart is 0", () => {
    const outOfStockHtml = sampleHtml
      .replace('value="1"', 'value="0"')
      .replace('"yes"', '"no"')
      .replace('prodQty = 5', 'prodQty = 0');

    const parser = new HMTInSource();
    const snapshot = parser.parseHtml(
      "https://hmtwatches.in/product_overview?id=789",
      outOfStockHtml
    );

    expect(snapshot.in_stock).toBe(false);
  });
});
