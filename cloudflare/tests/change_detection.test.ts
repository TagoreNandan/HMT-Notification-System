import { describe, expect, it } from "vitest";
import { createNotificationEvent, detectChanges } from "../src/polling/change_detection";
import { ProductSnapshot } from "../src/types";

describe("Change Detection Logic", () => {
  it("detects NEW_MODEL when previous snapshot is null", () => {
    const current: ProductSnapshot = {
      url: "https://hmtwatches.in/product_overview?id=123",
      title: "HMT Kohinoor Blue",
      price: 3200,
      in_stock: true,
      raw: {},
    };

    const changes = detectChanges(null, current);
    expect(changes).toHaveLength(1);
    expect(changes[0].change_type).toBe("new_model");
    expect(changes[0].new_value).toBe("HMT Kohinoor Blue");
  });

  it("detects BACK_IN_STOCK when transition is false -> true", () => {
    const previous: ProductSnapshot = {
      url: "https://hmtwatches.in/product_overview?id=123",
      title: "HMT Kohinoor Blue",
      price: 3200,
      in_stock: false,
      raw: {},
    };

    const current: ProductSnapshot = {
      ...previous,
      in_stock: true,
    };

    const changes = detectChanges(previous, current);
    expect(changes).toHaveLength(1);
    expect(changes[0].change_type).toBe("back_in_stock");
    expect(changes[0].old_value).toBe("out_of_stock");
    expect(changes[0].new_value).toBe("in_stock");
  });

  it("detects NO_CHANGE when in_stock remains true on consecutive polls", () => {
    const snapshot: ProductSnapshot = {
      url: "https://hmtwatches.in/product_overview?id=123",
      title: "HMT Kohinoor Blue",
      price: 3200,
      in_stock: true,
      raw: {},
    };

    const changes = detectChanges(snapshot, snapshot);
    expect(changes).toHaveLength(1);
    expect(changes[0].change_type).toBe("no_change");
  });

  it("detects OUT_OF_STOCK when transition is true -> false", () => {
    const previous: ProductSnapshot = {
      url: "https://hmtwatches.in/product_overview?id=123",
      title: "HMT Kohinoor Blue",
      price: 3200,
      in_stock: true,
      raw: {},
    };

    const current: ProductSnapshot = {
      ...previous,
      in_stock: false,
    };

    const changes = detectChanges(previous, current);
    expect(changes).toHaveLength(1);
    expect(changes[0].change_type).toBe("out_of_stock");
  });

  it("detects PRICE_CHANGE when price changes", () => {
    const previous: ProductSnapshot = {
      url: "https://hmtwatches.in/product_overview?id=123",
      title: "HMT Kohinoor Blue",
      price: 3200,
      in_stock: true,
      raw: {},
    };

    const current: ProductSnapshot = {
      ...previous,
      price: 3500,
    };

    const changes = detectChanges(previous, current);
    expect(changes).toHaveLength(1);
    expect(changes[0].change_type).toBe("price_change");
    expect(changes[0].old_value).toBe("3200");
    expect(changes[0].new_value).toBe("3500");
  });

  it("creates notification event with correct event_id formatting", () => {
    const change = { change_type: "back_in_stock" as const, old_value: "out_of_stock", new_value: "in_stock" };
    const event = createNotificationEvent(
      change,
      42,
      "HMT Tareeq Sunray Yellow",
      2400,
      true,
      "https://www.hmtwatches.store/product/tareeq-yellow",
      "hmt_store",
      "2026-09-27T12:00:00Z",
      "https://img.hmt.in/tareeq.jpg",
      "Tareeq",
      101
    );

    expect(event.event_id).toBe("evt_p42_snap_101_back_in_stock");
    expect(event.title).toBe("HMT Tareeq Sunray Yellow");
    expect(event.price).toBe(2400);
    expect(event.in_stock).toBe(true);
  });
});
