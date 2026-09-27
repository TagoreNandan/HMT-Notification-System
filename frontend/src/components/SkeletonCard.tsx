import React from "react";

export const SkeletonCard: React.FC = () => {
  return (
    <div
      style={{
        background: "#1f2937",
        borderRadius: "12px",
        border: "1px solid #374151",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
      }}
    >
      {/* Image Skeleton */}
      <div
        className="skeleton-pulse"
        style={{
          width: "100%",
          height: "160px",
          borderRadius: "8px",
          background: "#374151",
        }}
      />

      {/* Header Skeleton */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <div
          className="skeleton-pulse"
          style={{ width: "75%", height: "20px", borderRadius: "4px", background: "#374151" }}
        />
        <div style={{ display: "flex", gap: "8px" }}>
          <div
            className="skeleton-pulse"
            style={{ width: "80px", height: "16px", borderRadius: "12px", background: "#374151" }}
          />
          <div
            className="skeleton-pulse"
            style={{ width: "100px", height: "16px", borderRadius: "12px", background: "#374151" }}
          />
        </div>
      </div>

      {/* Price & Stock Row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div
          className="skeleton-pulse"
          style={{ width: "90px", height: "24px", borderRadius: "4px", background: "#374151" }}
        />
        <div
          className="skeleton-pulse"
          style={{ width: "100px", height: "24px", borderRadius: "12px", background: "#374151" }}
        />
      </div>

      {/* Button Skeleton */}
      <div
        className="skeleton-pulse"
        style={{ width: "100%", height: "40px", borderRadius: "8px", background: "#374151", marginTop: "auto" }}
      />
    </div>
  );
};
