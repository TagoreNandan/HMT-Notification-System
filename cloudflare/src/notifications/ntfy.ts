import { Env, NotificationEvent } from "../types";

export async function sendNtfyNotification(
  env: Env,
  event: NotificationEvent
): Promise<boolean> {
  if (!env.NTFY_TOPIC) {
    console.log("ntfy notification skipped: NTFY_TOPIC secret not set");
    return false;
  }

  const serverUrl = (env.NTFY_SERVER_URL || "https://ntfy.sh").replace(/\/$/, "");
  const topic = env.NTFY_TOPIC.replace(/^\//, "");
  const targetUrl = `${serverUrl}/${topic}`;

  const title = formatNtfyTitle(event);
  const body = formatNtfyBody(event);
  const tags = event.event_type === "back_in_stock" ? "watch,shopping_cart,rotating_light" : "watch,bell";

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const res = await fetch(targetUrl, {
        method: "POST",
        headers: {
          Title: title,
          Click: event.url,
          Tags: tags,
          Priority: event.event_type === "back_in_stock" ? "high" : "default",
          "Content-Type": "text/plain; charset=utf-8",
        },
        body: body,
      });

      if (res.ok) {
        console.log(`ntfy notification sent successfully to topic ${topic} for event ${event.event_id}`);
        return true;
      }

      if (res.status === 429 || res.status >= 500) {
        console.warn(`ntfy attempt ${attempt} returned status ${res.status}. Retrying...`);
        await new Promise((resolve) => setTimeout(resolve, attempt * 1000));
        continue;
      }

      const errBody = await res.text();
      console.error(`ntfy request failed with status ${res.status}: ${errBody}`);
      return false;
    } catch (err) {
      console.warn(`ntfy attempt ${attempt} encountered error:`, err);
      if (attempt === 3) return false;
      await new Promise((resolve) => setTimeout(resolve, attempt * 1000));
    }
  }

  return false;
}

function formatNtfyTitle(event: NotificationEvent): string {
  const priceStr = event.price ? ` (₹${event.price.toLocaleString("en-IN")})` : "";
  if (event.event_type === "back_in_stock") {
    return `🚨 BACK IN STOCK: ${event.title}${priceStr}`;
  }
  if (event.event_type === "new_model") {
    return `✨ NEW MODEL: ${event.title}${priceStr}`;
  }
  if (event.event_type === "price_change") {
    return `🏷️ PRICE CHANGE: ${event.title}${priceStr}`;
  }
  return `⌚ HMT ALERT: ${event.title}`;
}

function formatNtfyBody(event: NotificationEvent): string {
  const priceStr = event.price ? `Price: ₹${event.price.toLocaleString("en-IN")}` : "Price: N/A";
  const siteStr = `Source: ${event.site_name}`;
  const colStr = event.collection ? ` | Collection: ${event.collection}` : "";

  return `${event.title}\n${priceStr}\n${siteStr}${colStr}\nTap to open HMT website directly!`;
}
