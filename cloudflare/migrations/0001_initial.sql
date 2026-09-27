-- Initial D1 Migration for HMT Watch Notification System

CREATE TABLE IF NOT EXISTS catalog_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    site_name TEXT NOT NULL,
    title TEXT,
    price REAL,
    in_stock INTEGER NOT NULL DEFAULT 0,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_catalog_products_site_url ON catalog_products(site_name, url);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    price REAL,
    in_stock INTEGER NOT NULL,
    raw TEXT NOT NULL DEFAULT '{}',
    fetched_at TEXT NOT NULL,
    FOREIGN KEY(product_id) REFERENCES catalog_products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_product_fetched ON snapshots(product_id, fetched_at);

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
);

CREATE TABLE IF NOT EXISTS notification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    user_id INTEGER NOT NULL DEFAULT 1,
    channel_type TEXT NOT NULL,
    destination TEXT,
    sent_at TEXT NOT NULL,
    UNIQUE(event_id, channel_type, destination, user_id)
);

CREATE INDEX IF NOT EXISTS idx_notification_logs_lookup ON notification_logs(event_id, user_id, channel_type, destination);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL DEFAULT 1,
    catalog_product_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, catalog_product_id),
    FOREIGN KEY(catalog_product_id) REFERENCES catalog_products(id) ON DELETE CASCADE
);
