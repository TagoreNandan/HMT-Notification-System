export interface Env {
  DB: D1Database;
  ASSETS?: Fetcher;
  RESEND_API_KEY?: string;
  RESEND_TO_EMAIL?: string;
  RESEND_FROM_EMAIL?: string;
  NTFY_TOPIC?: string;
  NTFY_SERVER_URL?: string;
}

export interface DiscoveredProduct {
  source: string;
  source_product_id: string;
  title: string;
  normalized_title: string;
  url: string;
  collection?: string | null;
  image_url?: string | null;
  price?: number | null;
  in_stock: boolean;
}

export interface ProductSnapshot {
  url: string;
  title: string;
  price: number | null;
  in_stock: boolean;
  raw: Record<string, any>;
}

export type ChangeType =
  | "new_model"
  | "price_change"
  | "back_in_stock"
  | "out_of_stock"
  | "no_change";

export interface DetectedChange {
  change_type: ChangeType;
  old_value?: string | null;
  new_value?: string | null;
  details?: Record<string, any>;
}

export interface NotificationEvent {
  event_id: string;
  event_type: string;
  product_id: number;
  title: string;
  price: number | null;
  in_stock: boolean;
  url: string;
  site_name: string;
  occurred_at: string;
  image_url?: string | null;
  collection?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  details?: Record<string, any>;
}

export interface CatalogProductRow {
  id: number;
  url: string;
  site_name: string;
  title: string | null;
  price: number | null;
  in_stock: number;
  last_seen: string;
  created_at: string;
}

export interface SnapshotRow {
  id: number;
  product_id: number;
  title: string;
  price: number | null;
  in_stock: number;
  raw: string;
  fetched_at: string;
}

export interface ChangeEventRow {
  id: number;
  product_id: number;
  snapshot_id: number;
  change_type: string;
  old_value: string | null;
  new_value: string | null;
  details: string;
  created_at: string;
}

export interface NotificationLogRow {
  id: number;
  event_id: string;
  user_id: number;
  channel_type: string;
  destination: string | null;
  sent_at: string;
}

export interface WatchlistItemRow {
  id: number;
  user_id: number;
  catalog_product_id: number;
  created_at: string;
}

export interface PipelineStats {
  catalog_sync: { new: number; updated: number; unchanged: number };
  discovered_count: number;
  changes_count: number;
  events_count: number;
  dispatch_stats: { sent: number; suppressed: number; failed: number };
  execution_metrics?: {
    duration_ms: number;
    subrequests_count: number;
    d1_reads_count: number;
    d1_writes_count: number;
  };
}
