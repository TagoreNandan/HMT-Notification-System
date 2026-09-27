import React, { useState } from "react";
import type { CatalogProduct } from "../types";
import { parseCollection, formatPrice, formatTimeAgo, cleanStoreName } from "../utils";
import { WatchAvatar } from "./WatchAvatar";

interface ProductCardProps {
  product: CatalogProduct;
  isWatched: boolean;
  isLoading: boolean;
  onToggleWatch: (product: CatalogProduct) => void;
}

export const ProductCard: React.FC<ProductCardProps> = React.memo(
  ({ product, isWatched, isLoading, onToggleWatch }) => {
    const [imageError, setImageError] = useState(false);
    const collection = parseCollection(product.title);
    const store = cleanStoreName(product.url, product.site_name);

    return (
      <div
        style={{
          background: isWatched ? "#1e293b" : "#1f2937",
          borderRadius: "12px",
          border: isWatched
            ? "2px solid #10b981"
            : "1px solid #374151",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          gap: "14px",
          position: "relative",
          boxShadow: isWatched
            ? "0 4px 20px -2px rgba(16, 185, 129, 0.25)"
            : "0 2px 8px rgba(0, 0, 0, 0.2)",
          transition: "transform 0.2s, box-shadow 0.2s, border-color 0.2s",
        }}
      >
        {/* Watching Badge Indicator */}
        {isWatched && (
          <div
            style={{
              position: "absolute",
              top: "10px",
              right: "10px",
              zIndex: 2,
              background: "#10b981",
              color: "#064e3b",
              fontWeight: 800,
              fontSize: "11px",
              padding: "3px 8px",
              borderRadius: "12px",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
            }}
          >
            ★ Watching
          </div>
        )}

        {/* Thumbnail Image / Fallback Avatar */}
        <div style={{ position: "relative", width: "100%" }}>
          {product.image_url && !imageError ? (
            <img
              src={product.image_url}
              alt={product.title}
              loading="lazy"
              onError={() => setImageError(true)}
              style={{
                width: "100%",
                height: "160px",
                objectFit: "cover",
                borderRadius: "8px",
                background: "#111827",
              }}
            />
          ) : (
            <WatchAvatar title={product.title} inStock={product.in_stock} />
          )}
        </div>

        {/* Product Details Header */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px", flexWrap: "wrap" }}>
            <span
              style={{
                background: "#374151",
                color: "#d1d5db",
                fontSize: "11px",
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: "4px",
                textTransform: "uppercase",
              }}
            >
              {collection}
            </span>

            <span
              style={{
                background: "rgba(59, 130, 246, 0.15)",
                color: "#60a5fa",
                fontSize: "11px",
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: "4px",
              }}
            >
              {store}
            </span>
          </div>

          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            title="Open product page on HMT website"
            style={{
              fontSize: "17px",
              fontWeight: 700,
              color: "white",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              lineHeight: "1.3",
            }}
          >
            <span>{product.title}</span>
            <span style={{ fontSize: "14px", color: "#9ca3af" }}>↗</span>
          </a>
        </div>

        {/* Price & Stock Badge Row */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: "11px", color: "#9ca3af", textTransform: "uppercase" }}>Price</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "white" }}>
              {formatPrice(product.price)}
            </div>
          </div>

          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 12px",
              borderRadius: "20px",
              background: product.in_stock ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
              color: product.in_stock ? "#10b981" : "#ef4444",
              border: `1px solid ${product.in_stock ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)"}`,
              fontWeight: 700,
              fontSize: "13px",
            }}
          >
            <span>{product.in_stock ? "🟢" : "🔴"}</span>
            <span>{product.in_stock ? "In Stock" : "Out of Stock"}</span>
          </span>
        </div>

        {/* Last checked timestamp */}
        {product.last_seen && (
          <div style={{ fontSize: "12px", color: "#6b7280" }}>
            Last checked: {formatTimeAgo(product.last_seen)}
          </div>
        )}

        {/* Action Button: One Click Watch Toggle */}
        <button
          disabled={isLoading}
          onClick={() => onToggleWatch(product)}
          style={{
            background: isWatched ? "#10b981" : "#2563eb",
            color: isWatched ? "#064e3b" : "white",
            border: "none",
            padding: "10px 16px",
            borderRadius: "8px",
            cursor: isLoading ? "not-allowed" : "pointer",
            opacity: isLoading ? 0.7 : 1,
            fontWeight: 700,
            fontSize: "14px",
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            transition: "all 0.2s",
            marginTop: "4px",
          }}
        >
          {isLoading ? (
            <span>Updating...</span>
          ) : isWatched ? (
            <>
              <span>✓ Watching</span>
              <span style={{ fontSize: "11px", opacity: 0.8 }}>(Click to Stop)</span>
            </>
          ) : (
            <>
              <span>+ Watch Product</span>
            </>
          )}
        </button>
      </div>
    );
  }
);
ProductCard.displayName = "ProductCard";
