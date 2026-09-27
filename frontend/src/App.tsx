import { useEffect, useState, useMemo, useCallback } from "react";
import type { CatalogProduct, DashboardStats, StockFilter, StoreFilter, Toast } from "./types";
import { parseCollection, parseColor, cleanStoreName } from "./utils";
import { Navbar } from "./components/Navbar";
import { Dashboard } from "./components/Dashboard";
import { FilterBar } from "./components/FilterBar";
import { ProductCard } from "./components/ProductCard";
import { SkeletonCard } from "./components/SkeletonCard";
import { EmptyState } from "./components/EmptyState";
import { ToastContainer } from "./components/ToastContainer";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export default function App() {
  const [catalog, setCatalog] = useState<CatalogProduct[]>([]);
  const [watchlist, setWatchlist] = useState<number[]>([]);
  const [isCatalogLoading, setIsCatalogLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  // Search & Filters State
  const [search, setSearch] = useState("");
  const [stockFilter, setStockFilter] = useState<StockFilter>("all");
  const [storeFilter, setStoreFilter] = useState<StoreFilter>("all");
  const [collectionFilter, setCollectionFilter] = useState("all");

  // Dashboard & Status State
  const [statusMeta, setStatusMeta] = useState<{
    last_catalog_sync: string | null;
    last_poll: string | null;
    next_poll_seconds: number;
  }>({
    last_catalog_sync: null,
    last_poll: null,
    next_poll_seconds: 900,
  });

  const [nextPollCountdown, setNextPollCountdown] = useState<number>(900);

  // Toast Notifications State
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: Toast["type"] = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Fetch Catalog Data
  const loadCatalog = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/catalog`);
      if (!res.ok) throw new Error("Failed to load catalog");
      const data = await res.json();
      setCatalog(data);
    } catch (err) {
      console.error(err);
      addToast("Failed to connect to backend server", "error");
    }
  }, [addToast]);

  // Fetch Watchlist Data
  const loadWatchlist = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/watchlist`);
      if (!res.ok) throw new Error("Failed to load watchlist");
      const data = await res.json();
      setWatchlist(data.map((p: { id: number }) => p.id));
    } catch (err) {
      console.error(err);
    }
  }, []);

  // Fetch Status Metadata
  const loadStatusMeta = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/catalog/status`);
      if (res.ok) {
        const meta = await res.json();
        setStatusMeta({
          last_catalog_sync: meta.last_catalog_sync,
          last_poll: meta.last_poll,
          next_poll_seconds: meta.next_poll_seconds,
        });
        setNextPollCountdown(meta.next_poll_seconds || 900);
      }
    } catch (err) {
      console.error(err);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    async function init() {
      setIsCatalogLoading(true);
      await Promise.all([loadCatalog(), loadWatchlist(), loadStatusMeta()]);
      setIsCatalogLoading(false);
    }
    init();
  }, [loadCatalog, loadWatchlist, loadStatusMeta]);

  // Next Poll Countdown Timer
  useEffect(() => {
    const timer = setInterval(() => {
      setNextPollCountdown((prev) => {
        if (prev <= 1) {
          loadCatalog();
          loadStatusMeta();
          addToast("Polling cycle completed", "info");
          return 900;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [loadCatalog, loadStatusMeta, addToast]);

  // Manual Catalog Refresh Trigger
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch(`${API_BASE}/catalog/sync`, { method: "POST" });
      if (!res.ok) throw new Error("Sync failed");
      await Promise.all([loadCatalog(), loadWatchlist(), loadStatusMeta()]);
      addToast("Catalog synced successfully!", "success");
    } catch (err) {
      console.error(err);
      addToast("Failed to refresh catalog", "error");
    } finally {
      setIsRefreshing(false);
    }
  };

  // One Click Watchlist Toggle (Requirement 2)
  const handleToggleWatch = async (product: CatalogProduct) => {
    setActionLoadingId(product.id);
    const isCurrentlyWatched = watchlist.includes(product.id);

    try {
      if (isCurrentlyWatched) {
        const res = await fetch(`${API_BASE}/watchlist/${product.id}`, {
          method: "DELETE",
        });
        if (!res.ok) throw new Error("Failed to remove watch");
        setWatchlist((prev) => prev.filter((id) => id !== product.id));
        addToast(`Removed "${product.title}" from watchlist`, "info");
      } else {
        const res = await fetch(`${API_BASE}/watchlist/${product.id}`, {
          method: "POST",
        });
        if (!res.ok) throw new Error("Failed to add watch");
        setWatchlist((prev) => [...prev, product.id]);
        addToast(`Added "${product.title}" to watchlist!`, "success");
      }
    } catch (err) {
      console.error(err);
      addToast("Failed to update watchlist", "error");
    } finally {
      setActionLoadingId(null);
    }
  };

  // Derive unique collections list dynamically
  const collections = useMemo(() => {
    const set = new Set<string>();
    catalog.forEach((p) => {
      set.add(parseCollection(p.title));
    });
    return Array.from(set).sort();
  }, [catalog]);

  // Compute Filter Stock Counts
  const filterCounts = useMemo(() => {
    let inStockCount = 0;
    let outOfStockCount = 0;
    let watchingCount = 0;

    catalog.forEach((p) => {
      if (p.in_stock) inStockCount++;
      else outOfStockCount++;
      if (watchlist.includes(p.id)) watchingCount++;
    });

    return {
      all: catalog.length,
      in_stock: inStockCount,
      out_of_stock: outOfStockCount,
      watching: watchingCount,
    };
  }, [catalog, watchlist]);

  // Dashboard Stats Object
  const dashboardStats: DashboardStats = useMemo(() => {
    return {
      total_watches: catalog.length,
      in_stock: filterCounts.in_stock,
      out_of_stock: filterCounts.out_of_stock,
      watching: watchlist.length,
      last_catalog_sync: statusMeta.last_catalog_sync,
      last_poll: statusMeta.last_poll,
      next_poll_seconds: nextPollCountdown,
      is_monitoring: true,
    };
  }, [catalog.length, filterCounts, watchlist.length, statusMeta, nextPollCountdown]);

  // Instant Multi-Property Search & Filter (Requirement 3 & 4)
  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return catalog
      .filter((p) => {
        // Search matching
        if (query) {
          const col = parseCollection(p.title).toLowerCase();
          const color = parseColor(p.title).toLowerCase();
          const store = cleanStoreName(p.url, p.site_name).toLowerCase();
          const title = p.title.toLowerCase();

          const matchesSearch =
            title.includes(query) ||
            col.includes(query) ||
            color.includes(query) ||
            store.includes(query);

          if (!matchesSearch) return false;
        }

        // Stock Filter
        if (stockFilter === "in_stock" && !p.in_stock) return false;
        if (stockFilter === "out_of_stock" && p.in_stock) return false;
        if (stockFilter === "watching" && !watchlist.includes(p.id)) return false;

        // Store Filter
        if (storeFilter !== "all") {
          const storeName = cleanStoreName(p.url, p.site_name);
          if (storeName !== storeFilter) return false;
        }

        // Collection Filter
        if (collectionFilter !== "all") {
          const col = parseCollection(p.title);
          if (col !== collectionFilter) return false;
        }

        return true;
      })
      .sort((a, b) => {
        // Watched items first
        const aw = watchlist.includes(a.id);
        const bw = watchlist.includes(b.id);
        if (aw !== bw) return aw ? -1 : 1;

        // In-stock items next
        if (a.in_stock !== b.in_stock) {
          return Number(b.in_stock) - Number(a.in_stock);
        }

        // Alphabetical
        return a.title.localeCompare(b.title);
      });
  }, [catalog, watchlist, search, stockFilter, storeFilter, collectionFilter]);

  const hasActiveFilters =
    search !== "" ||
    stockFilter !== "all" ||
    storeFilter !== "all" ||
    collectionFilter !== "all";

  const handleResetFilters = useCallback(() => {
    setSearch("");
    setStockFilter("all");
    setStoreFilter("all");
    setCollectionFilter("all");
  }, []);

  return (
    <div>
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header & Poll Status */}
      <Navbar
        lastPoll={dashboardStats.last_poll}
        nextPollSeconds={nextPollCountdown}
        isRefreshing={isRefreshing}
        onRefresh={handleManualRefresh}
      />

      {/* Dashboard Statistics */}
      <Dashboard stats={dashboardStats} />

      {/* Instant Search & Filter Bar */}
      <FilterBar
        search={search}
        onSearchChange={setSearch}
        stockFilter={stockFilter}
        onStockFilterChange={setStockFilter}
        storeFilter={storeFilter}
        onStoreFilterChange={setStoreFilter}
        collectionFilter={collectionFilter}
        onCollectionFilterChange={setCollectionFilter}
        collections={collections}
        counts={filterCounts}
        onReset={handleResetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      {/* Products Counter / Summary */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
          color: "#9ca3af",
          fontSize: "14px",
        }}
      >
        <div>
          Showing <strong>{filteredProducts.length}</strong> of{" "}
          <strong>{catalog.length}</strong> watches
        </div>
        {watchlist.length > 0 && (
          <div>
            Monitoring <strong>{watchlist.length}</strong> selected watches
          </div>
        )}
      </div>

      {/* Product Card Grid or Skeleton / Empty States */}
      {isCatalogLoading ? (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "20px",
          }}
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filteredProducts.length === 0 ? (
        <EmptyState onReset={handleResetFilters} searchQuery={search} />
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "20px",
          }}
        >
          {filteredProducts.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              isWatched={watchlist.includes(product.id)}
              isLoading={actionLoadingId === product.id}
              onToggleWatch={handleToggleWatch}
            />
          ))}
        </div>
      )}
    </div>
  );
}