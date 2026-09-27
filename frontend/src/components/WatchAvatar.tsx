import React from "react";

interface WatchAvatarProps {
  title: string;
  inStock: boolean;
}

export const WatchAvatar: React.FC<WatchAvatarProps> = React.memo(
  ({ title, inStock }) => {
    // Generate deterministic background gradient from watch title
    let hash = 0;
    for (let i = 0; i < title.length; i++) {
      hash = title.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue1 = Math.abs(hash % 360);
    const hue2 = (hue1 + 40) % 360;

    return (
      <div
        style={{
          width: "100%",
          height: "160px",
          borderRadius: "8px",
          background: `linear-gradient(135deg, hsl(${hue1}, 40%, 18%), hsl(${hue2}, 50%, 12%))`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          overflow: "hidden",
          border: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        {/* Subtle dial background ring */}
        <div
          style={{
            width: "100px",
            height: "100px",
            borderRadius: "50%",
            border: "2px dashed rgba(255, 255, 255, 0.15)",
            position: "absolute",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        />

        {/* Watch SVG Dial */}
        <svg
          width="64"
          height="64"
          viewBox="0 0 24 24"
          fill="none"
          stroke={inStock ? "#10b981" : "#9ca3af"}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.5))" }}
        >
          <circle cx="12" cy="12" r="9" />
          <polyline points="12 7 12 12 15 15" />
          <path d="M12 2v1" />
          <path d="M12 21v1" />
          <path d="M2 12h1" />
          <path d="M21 12h1" />
        </svg>

        {/* Brand Stamp */}
        <div
          style={{
            position: "absolute",
            bottom: "8px",
            fontSize: "10px",
            fontWeight: 700,
            letterSpacing: "1.5px",
            color: "rgba(255, 255, 255, 0.4)",
            textTransform: "uppercase",
          }}
        >
          HMT AUTOMATIC
        </div>
      </div>
    );
  }
);
WatchAvatar.displayName = "WatchAvatar";
