import { CatalogProductRow, SnapshotRow, Env } from "../types";

export class DBQueries {
  constructor(private db: D1Database) {}

  async initTables(): Promise<void> {
    await this.db.batch([
      this.db.prepare(`
        CREATE TABLE IF NOT EXISTS catalog_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            site_name TEXT NOT NULL,
            title TEXT,
            price REAL,
            in_stock INTEGER NOT NULL DEFAULT 0,
            last_seen TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
      `),
      this.db.prepare(`
        CREATE INDEX IF NOT EXISTS idx_catalog_products_site_url ON catalog_products(site_name, url)
      `),
      this.db.prepare(`
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            price REAL,
            in_stock INTEGER NOT NULL,
            raw TEXT NOT NULL DEFAULT '{}',
            fetched_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES catalog_products(id) ON DELETE CASCADE
        )
      `),
      this.db.prepare(`
        CREATE INDEX IF NOT EXISTS idx_snapshots_product_fetched ON snapshots(product_id, fetched_at)
      `),
      this.db.prepare(`
        CREATE TABLE IF NOT EXISTS change_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            snapshot_id INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            details TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES catalog_products(id) ON DELETE CASCADE
        )
      `),
      this.db.prepare(`
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            user_id INTEGER NOT NULL DEFAULT 1,
            channel_type TEXT NOT NULL,
            destination TEXT,
            sent_at TEXT NOT NULL,
            UNIQUE(event_id, channel_type, destination, user_id)
        )
      `),
      this.db.prepare(`
        CREATE INDEX IF NOT EXISTS idx_notification_logs_lookup ON notification_logs(event_id, user_id, channel_type, destination)
      `),
      this.db.prepare(`
        CREATE TABLE IF NOT EXISTS watchlist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            catalog_product_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, catalog_product_id),
            FOREIGN KEY(catalog_product_id) REFERENCES catalog_products(id) ON DELETE CASCADE
        )
      `),
    ]);
  }

  async getAllCatalogProducts(): Promise<CatalogProductRow[]> {
    const { results } = await this.db
      .prepare("SELECT * FROM catalog_products ORDER BY title ASC")
      .all<CatalogProductRow>();
    return results || [];
  }

  async getCatalogProductByUrl(url: string): Promise<CatalogProductRow | null> {
    return (
      (await this.db
        .prepare("SELECT * FROM catalog_products WHERE url = ? LIMIT 1")
        .bind(url)
        .first<CatalogProductRow>()) || null
    );
  }

  async insertCatalogProduct(
    url: string,
    siteName: string,
    title: string,
    price: number | null,
    inStock: boolean,
    nowIso: string
  ): Promise<CatalogProductRow> {
    await this.db
      .prepare(
        `INSERT INTO catalog_products (url, site_name, title, price, in_stock, last_seen, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(url, siteName, title, price, inStock ? 1 : 0, nowIso, nowIso)
      .run();

    const inserted = await this.getCatalogProductByUrl(url);
    if (!inserted) throw new Error(`Failed to insert catalog product: ${url}`);
    return inserted;
  }

  async updateCatalogProduct(
    id: number,
    title: string,
    price: number | null,
    inStock: boolean,
    nowIso: string
  ): Promise<void> {
    await this.db
      .prepare(
        `UPDATE catalog_products 
         SET title = ?, price = ?, in_stock = ?, last_seen = ? 
         WHERE id = ?`
      )
      .bind(title, price, inStock ? 1 : 0, nowIso, id)
      .run();
  }

  async getLatestSnapshot(productId: number): Promise<SnapshotRow | null> {
    return (
      (await this.db
        .prepare(
          "SELECT * FROM snapshots WHERE product_id = ? ORDER BY fetched_at DESC LIMIT 1"
        )
        .bind(productId)
        .first<SnapshotRow>()) || null
    );
  }

  async insertSnapshot(
    productId: number,
    title: string,
    price: number | null,
    inStock: boolean,
    rawJson: string,
    fetchedAtIso: string
  ): Promise<number> {
    const res = await this.db
      .prepare(
        `INSERT INTO snapshots (product_id, title, price, in_stock, raw, fetched_at)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
      .bind(productId, title, price, inStock ? 1 : 0, rawJson, fetchedAtIso)
      .run();

    return Number(res.meta.last_row_id);
  }

  async insertChangeEvent(
    productId: number,
    snapshotId: number,
    changeType: string,
    oldValue: string | null,
    newValue: string | null,
    detailsJson: string,
    createdAtIso: string
  ): Promise<void> {
    await this.db
      .prepare(
        `INSERT INTO change_events (product_id, snapshot_id, change_type, old_value, new_value, details, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        productId,
        snapshotId,
        changeType,
        oldValue,
        newValue,
        detailsJson,
        createdAtIso
      )
      .run();
  }

  async logNotificationAttempt(
    eventId: string,
    userId: number,
    channelType: string,
    destination: string | null,
    sentAtIso: string
  ): Promise<boolean> {
    try {
      await this.db
        .prepare(
          `INSERT INTO notification_logs (event_id, user_id, channel_type, destination, sent_at)
           VALUES (?, ?, ?, ?, ?)`
        )
        .bind(eventId, userId, channelType, destination, sentAtIso)
        .run();
      return true;
    } catch (err: any) {
      // UNIQUE constraint failed -> duplicate notification suppressed!
      if (err?.message?.includes("UNIQUE constraint failed")) {
        return false;
      }
      throw err;
    }
  }

  async isNotificationLogged(
    eventId: string,
    userId: number,
    channelType: string,
    destination: string | null
  ): Promise<boolean> {
    const row = await this.db
      .prepare(
        `SELECT id FROM notification_logs 
         WHERE event_id = ? AND user_id = ? AND channel_type = ? AND (destination = ? OR (destination IS NULL AND ? IS NULL))
         LIMIT 1`
      )
      .bind(eventId, userId, channelType, destination, destination)
      .first();
    return !!row;
  }

  async getWatchlist(userId: number = 7): Promise<CatalogProductRow[]> {
    const { results } = await this.db
      .prepare(
        `SELECT cp.* FROM catalog_products cp
         INNER JOIN watchlist_items wi ON wi.catalog_product_id = cp.id
         WHERE wi.user_id = ?
         ORDER BY cp.title ASC`
      )
      .bind(userId)
      .all<CatalogProductRow>();
    return results || [];
  }

  async addWatchlistItem(catalogProductId: number, userId: number = 7): Promise<boolean> {
    try {
      await this.db
        .prepare(
          `INSERT INTO watchlist_items (user_id, catalog_product_id, created_at)
           VALUES (?, ?, ?)`
        )
        .bind(userId, catalogProductId, new Date().toISOString())
        .run();
      return true;
    } catch (err: any) {
      if (err?.message?.includes("UNIQUE constraint failed")) {
        return false;
      }
      throw err;
    }
  }

  async removeWatchlistItem(catalogProductId: number, userId: number = 7): Promise<boolean> {
    const res = await this.db
      .prepare(
        `DELETE FROM watchlist_items WHERE user_id = ? AND catalog_product_id = ?`
      )
      .bind(userId, catalogProductId)
      .run();
    return (res.meta.changes || 0) > 0;
  }

  async getCatalogStatus(): Promise<{
    total_watches: number;
    in_stock: number;
    out_of_stock: number;
    last_catalog_sync: string | null;
    last_poll: string | null;
    next_poll_seconds: number;
  }> {
    const totalRow = await this.db
      .prepare("SELECT COUNT(*) as cnt FROM catalog_products")
      .first<{ cnt: number }>();
    const inStockRow = await this.db
      .prepare("SELECT COUNT(*) as cnt FROM catalog_products WHERE in_stock = 1")
      .first<{ cnt: number }>();

    const total = totalRow?.cnt || 0;
    const inStock = inStockRow?.cnt || 0;
    const outOfStock = total - inStock;

    const lastSeenRow = await this.db
      .prepare("SELECT MAX(last_seen) as max_seen FROM catalog_products")
      .first<{ max_seen: string | null }>();
    const lastFetchedRow = await this.db
      .prepare("SELECT MAX(fetched_at) as max_fetched FROM snapshots")
      .first<{ max_fetched: string | null }>();

    const lastSync = lastSeenRow?.max_seen || null;
    const lastPoll = lastFetchedRow?.max_fetched || lastSync || new Date().toISOString();

    const lastPollDate = lastPoll ? new Date(lastPoll) : new Date();
    const elapsedSec = Math.floor((Date.now() - lastPollDate.getTime()) / 1000);
    const pollInterval = 120; // 2 minutes requirement
    const nextPollSeconds = Math.max(0, pollInterval - (elapsedSec % pollInterval));

    return {
      total_watches: total,
      in_stock: inStock,
      out_of_stock: outOfStock,
      last_catalog_sync: lastSync,
      last_poll: lastPoll,
      next_poll_seconds: nextPollSeconds,
    };
  }
}
