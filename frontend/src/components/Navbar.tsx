import React from "react";
import { formatTimeAgo, formatCountdown } from "../utils";

interface NavbarProps {
  lastPoll?: string | null;
  nextPollSeconds: number;
  isRefreshing: boolean;
  onRefresh: () => void;
}

export const Navbar: React.FC<NavbarProps> = React.memo(
  ({ lastPoll, nextPollSeconds, isRefreshing, onRefresh }) => {
    return (
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
          paddingBottom: "24px",
          borderBottom: "1px solid #1f2937",
          marginBottom: "24px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "32px" }}>⌚</span>
            <h1
              style={{
                fontSize: "28px",
                fontWeight: 800,
                color: "white",
                margin: 0,
                letterSpacing: "-0.5px",
              }}
            >
              HMT Watch Monitor
            </h1>
          </div>
          <p style={{ color: "#9ca3af", fontSize: "14px", marginTop: "4px", margin: 0 }}>
            Real-time stock and price change notifications for HMT timepieces.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
          {/* Status Badge Indicator */}
          <div
            style={{
              background: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "10px",
              padding: "8px 14px",
              display: "flex",
              alignItems: "center",
              gap: "12px",
              fontSize: "13px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  background: "#10b981",
                  boxShadow: "0 0 10px #10b981",
                  display: "inline-block",
                  animation: "pulseGlow 2s infinite",
                }}
              />
              <span style={{ fontWeight: 700, color: "#10b981" }}>Monitoring</span>
            </div>

            <div style={{ width: "1px", height: "16px", background: "#374151" }} />

            <div style={{ color: "#9ca3af" }}>
              Last checked:{" "}
              <strong style={{ color: "#e5e7eb" }}>{formatTimeAgo(lastPoll)}</strong>
            </div>

            <div style={{ width: "1px", height: "16px", background: "#374151" }} />

            <div style={{ color: "#9ca3af" }}>
              Next poll:{" "}
              <strong style={{ color: "#3b82f6" }}>{formatCountdown(nextPollSeconds)}</strong>
            </div>
          </div>

          {/* Sync Button */}
          <button
            disabled={isRefreshing}
            onClick={onRefresh}
            style={{
              background: isRefreshing ? "#374151" : "#2563eb",
              color: "white",
              border: "none",
              padding: "10px 18px",
              borderRadius: "8px",
              fontWeight: 600,
              fontSize: "14px",
              cursor: isRefreshing ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              transition: "all 0.2s",
            }}
          >
            <span
              style={{
                display: "inline-block",
                animation: isRefreshing ? "spin 1s linear infinite" : "none",
              }}
            >
              🔄
            </span>
            {isRefreshing ? "Syncing..." : "Sync Catalog"}
          </button>
        </div>
      </header>
    );
  }
);
Navbar.displayName = "Navbar";
