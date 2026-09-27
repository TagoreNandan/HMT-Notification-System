import {
  DetectedChange,
  NotificationEvent,
  ProductSnapshot,
} from "../types";

export function detectChanges(
  previous: ProductSnapshot | null,
  current: ProductSnapshot
): DetectedChange[] {
  if (previous === null) {
    return [
      {
        change_type: "new_model",
        new_value: current.title,
        details: { reason: "new_model" },
      },
    ];
  }

  const changes: DetectedChange[] = [];

  const prevPrice = previous.price;
  const currPrice = current.price;
  if (prevPrice !== currPrice) {
    changes.push({
      change_type: "price_change",
      old_value: prevPrice !== null ? String(prevPrice) : null,
      new_value: currPrice !== null ? String(currPrice) : null,
      details: {},
    });
  }

  if (previous.in_stock !== current.in_stock) {
    if (current.in_stock) {
      changes.push({
        change_type: "back_in_stock",
        old_value: "out_of_stock",
        new_value: "in_stock",
      });
    } else {
      changes.push({
        change_type: "out_of_stock",
        old_value: "in_stock",
        new_value: "out_of_stock",
      });
    }
  }

  if (changes.length === 0) {
    changes.push({ change_type: "no_change" });
  }

  return changes;
}

export function createNotificationEvent(
  change: DetectedChange,
  productId: number,
  title: string,
  price: number | null,
  inStock: boolean,
  url: string,
  siteName: string,
  occurredAtIso?: string,
  imageUrl?: string | null,
  collection?: string | null,
  snapshotId?: number | null
): NotificationEvent {
  const nowIso = occurredAtIso || new Date().toISOString();
  const snapPart = snapshotId !== null && snapshotId !== undefined ? `_snap_${snapshotId}` : "";
  const eventId = `evt_p${productId}${snapPart}_${change.change_type}`;

  return {
    event_id: eventId,
    event_type: change.change_type,
    product_id: productId,
    title: title || "Tracked Product",
    price: price,
    in_stock: inStock,
    url: url,
    site_name: siteName,
    occurred_at: nowIso,
    image_url: imageUrl || null,
    collection: collection || null,
    old_value: change.old_value || null,
    new_value: change.new_value || null,
    details: change.details || {},
  };
}
