export type CatalogProduct = {
  id: number;
  title: string;
  url: string;
  in_stock: boolean;
  price?: number | null;
  site_name?: string;
  last_seen?: string | null;
  created_at?: string | null;
  image_url?: string | null;
};

export type DashboardStats = {
  total_watches: number;
  in_stock: number;
  out_of_stock: number;
  watching: number;
  last_catalog_sync: string | null;
  last_poll: string | null;
  next_poll_seconds: number;
  is_monitoring: boolean;
};

export type Toast = {
  id: string;
  message: string;
  type: "success" | "info" | "warning" | "error";
};

export type StockFilter = "all" | "in_stock" | "out_of_stock" | "watching";
export type StoreFilter = "all" | "hmtwatches.in" | "hmtwatches.store";
