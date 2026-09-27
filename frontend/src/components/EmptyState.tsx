import React from "react";

interface EmptyStateProps {
  onReset: () => void;
  searchQuery?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = React.memo(
  ({ onReset, searchQuery }) => {
    return (
      <div
        style={{
          background: "#1f2937",
          border: "1px dashed #374151",
          borderRadius: "16px",
          padding: "48px 24px",
          textAlign: "center",
          margin: "32px 0",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "16px",
        }}
      >
        <div
          style={{
            width: "64px",
            height: "64px",
            borderRadius: "50%",
            background: "rgba(55, 65, 81, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "28px",
          }}
        >
          🔍
        </div>

        <div style={{ maxWidth: "420px" }}>
          <h3 style={{ fontSize: "20px", fontWeight: 600, color: "white", marginBottom: "8px" }}>
            No watches match your search
          </h3>
          <p style={{ color: "#9ca3af", fontSize: "14px", lineHeight: "1.5" }}>
            {searchQuery
              ? `We couldn't find any watches matching "${searchQuery}". Try searching for a different model name, collection, or color.`
              : "No watches match the active filter criteria. Try adjusting or clearing your filters."}
          </p>
        </div>

        <button
          onClick={onReset}
          style={{
            background: "#2563eb",
            color: "white",
            border: "none",
            padding: "10px 20px",
            borderRadius: "8px",
            fontWeight: 600,
            fontSize: "14px",
            cursor: "pointer",
            transition: "background 0.2s",
            marginTop: "8px",
          }}
        >
          Reset All Filters
        </button>
      </div>
    );
  }
);
EmptyState.displayName = "EmptyState";
