import React from "react";
import type { DashboardStats } from "../types";
import { formatTimeAgo, formatCountdown } from "../utils";

interface DashboardProps {
  stats: DashboardStats;
}

export const Dashboard: React.FC<DashboardProps> = React.memo(({ stats }) => {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
        gap: "12px",
        marginBottom: "24px",
      }}
    >
      {/* Total Watches */}
      <div
        style={{
          background: "#1f2937",
          border: "1px solid #374151",
          borderRadius: "10px",
          padding: "14px",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#9ca3af", textTransform: "uppercase" }}>
          Total Watches
        </div>
        <div style={{ fontSize: "24px", fontWeight: 800, color: "white", marginTop: "4px" }}>
          {stats.total_watches}
        </div>
      </div>

      {/* Currently In Stock */}
      <div
        style={{
          background: "rgba(16, 185, 129, 0.08)",
          border: "1px solid rgba(16, 185, 129, 0.3)",
          borderRadius: "10px",
          padding: "14px",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#10b981", textTransform: "uppercase" }}>
          In Stock
        </div>
        <div style={{ fontSize: "24px", fontWeight: 800, color: "#10b981", marginTop: "4px" }}>
          {stats.in_stock}
        </div>
      </div>

      {/* Currently Out of Stock */}
      <div
        style={{
          background: "rgba(239, 68, 68, 0.08)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: "10px",
          padding: "14px",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#ef4444", textTransform: "uppercase" }}>
          Out of Stock
        </div>
        <div style={{ fontSize: "24px", fontWeight: 800, color: "#ef4444", marginTop: "4px" }}>
          {stats.out_of_stock}
        </div>
      </div>

      {/* Watching */}
      <div
        style={{
          background: "rgba(59, 130, 246, 0.08)",
          border: "1px solid rgba(59, 130, 246, 0.3)",
          borderRadius: "10px",
          padding: "14px",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#3b82f6", textTransform: "uppercase" }}>
          Watching
        </div>
        <div style={{ fontSize: "24px", fontWeight: 800, color: "#3b82f6", marginTop: "4px" }}>
          {stats.watching}
        </div>
      </div>

      {/* Last Catalog Sync */}
      <div
        style={{
          background: "#1f2937",
          border: "1px solid #374151",
          borderRadius: "10px",
          padding: "14px",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#9ca3af", textTransform: "uppercase" }}>
          Last Sync
        </div>
        <div style={{ fontSize: "15px", fontWeight: 700, color: "#e5e7eb", marginTop: "8px" }}>
          {formatTimeAgo(stats.last_catalog_sync)}
        </div>
      </div>

      {/* Last Poll */}
      <div
        style={{
          background: "#1f2937",
          border: "1px solid #374151",
          borderRadius: "10px",
          padding: "14px",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#9ca3af", textTransform: "uppercase" }}>
          Last Poll
        </div>
        <div style={{ fontSize: "15px", fontWeight: 700, color: "#e5e7eb", marginTop: "8px" }}>
          {formatTimeAgo(stats.last_poll)}
        </div>
      </div>

      {/* Next Poll */}
      <div
        style={{
          background: "#1f2937",
          border: "1px solid #374151",
          borderRadius: "10px",
          padding: "14px",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#9ca3af", textTransform: "uppercase" }}>
          Next Poll
        </div>
        <div style={{ fontSize: "15px", fontWeight: 700, color: "#60a5fa", marginTop: "8px" }}>
          {formatCountdown(stats.next_poll_seconds)}
        </div>
      </div>
    </div>
  );
});
Dashboard.displayName = "Dashboard";
