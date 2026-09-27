import React from "react";
import type { StockFilter, StoreFilter } from "../types";

interface FilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  stockFilter: StockFilter;
  onStockFilterChange: (filter: StockFilter) => void;
  storeFilter: StoreFilter;
  onStoreFilterChange: (filter: StoreFilter) => void;
  collectionFilter: string;
  onCollectionFilterChange: (collection: string) => void;
  collections: string[];
  counts: {
    all: number;
    in_stock: number;
    out_of_stock: number;
    watching: number;
  };
  onReset: () => void;
  hasActiveFilters: boolean;
}

export const FilterBar: React.FC<FilterBarProps> = React.memo(
  ({
    search,
    onSearchChange,
    stockFilter,
    onStockFilterChange,
    storeFilter,
    onStoreFilterChange,
    collectionFilter,
    onCollectionFilterChange,
    collections,
    counts,
    onReset,
    hasActiveFilters,
  }) => {
    return (
      <div
        style={{
          background: "#1f2937",
          border: "1px solid #374151",
          borderRadius: "14px",
          padding: "16px",
          marginBottom: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {/* Search Input Row */}
        <div style={{ position: "relative", width: "100%" }}>
          <span
            style={{
              position: "absolute",
              left: "14px",
              top: "50%",
              transform: "translateY(-50%)",
              fontSize: "16px",
              color: "#9ca3af",
              pointerEvents: "none",
            }}
          >
            🔍
          </span>
          <input
            type="text"
            placeholder="Search by model, collection, color (e.g. Tareeq, Stellar, Blue)..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 40px 12px 42px",
              borderRadius: "10px",
              border: "1px solid #374151",
              background: "#111827",
              color: "white",
              fontSize: "15px",
              boxSizing: "border-box",
              outline: "none",
              transition: "border-color 0.2s",
            }}
          />
          {search && (
            <button
              onClick={() => onSearchChange("")}
              style={{
                position: "absolute",
                right: "12px",
                top: "50%",
                transform: "translateY(-50%)",
                background: "transparent",
                border: "none",
                color: "#9ca3af",
                cursor: "pointer",
                fontSize: "16px",
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Filter Controls Row */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          {/* Stock Status Pills */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {(
              [
                { id: "all", label: "All", count: counts.all },
                { id: "in_stock", label: "🟢 In Stock", count: counts.in_stock },
                { id: "out_of_stock", label: "🔴 Out of Stock", count: counts.out_of_stock },
                { id: "watching", label: "★ Watching", count: counts.watching },
              ] as const
            ).map((item) => {
              const active = stockFilter === item.id;
              let activeBg = "#374151";
              if (active) {
                if (item.id === "in_stock") activeBg = "#065f46";
                else if (item.id === "out_of_stock") activeBg = "#991b1b";
                else if (item.id === "watching") activeBg = "#1e40af";
                else activeBg = "#2563eb";
              }

              return (
                <button
                  key={item.id}
                  onClick={() => onStockFilterChange(item.id as StockFilter)}
                  style={{
                    background: active ? activeBg : "#111827",
                    color: active ? "white" : "#9ca3af",
                    border: `1px solid ${active ? activeBg : "#374151"}`,
                    padding: "6px 12px",
                    borderRadius: "20px",
                    fontSize: "13px",
                    fontWeight: active ? 600 : 500,
                    cursor: "pointer",
                    transition: "all 0.15s",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>{item.label}</span>
                  <span
                    style={{
                      background: "rgba(255, 255, 255, 0.15)",
                      padding: "1px 6px",
                      borderRadius: "10px",
                      fontSize: "11px",
                    }}
                  >
                    {item.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Store & Collection Selectors */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
            {/* Store Select */}
            <select
              value={storeFilter}
              onChange={(e) => onStoreFilterChange(e.target.value as StoreFilter)}
              style={{
                background: "#111827",
                color: "white",
                border: "1px solid #374151",
                padding: "7px 12px",
                borderRadius: "8px",
                fontSize: "13px",
                fontWeight: 500,
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="all">All Stores</option>
              <option value="hmtwatches.in">hmtwatches.in</option>
              <option value="hmtwatches.store">hmtwatches.store</option>
            </select>

            {/* Collection Select */}
            <select
              value={collectionFilter}
              onChange={(e) => onCollectionFilterChange(e.target.value)}
              style={{
                background: "#111827",
                color: "white",
                border: "1px solid #374151",
                padding: "7px 12px",
                borderRadius: "8px",
                fontSize: "13px",
                fontWeight: 500,
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="all">All Collections</option>
              {collections.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>

            {/* Reset Filter Button */}
            {hasActiveFilters && (
              <button
                onClick={onReset}
                style={{
                  background: "transparent",
                  color: "#ef4444",
                  border: "1px solid rgba(239, 68, 68, 0.4)",
                  padding: "6px 12px",
                  borderRadius: "8px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }
);
FilterBar.displayName = "FilterBar";
