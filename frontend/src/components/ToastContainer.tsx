import React from "react";
import type { Toast } from "../types";

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = React.memo(
  ({ toasts, onDismiss }) => {
    if (toasts.length === 0) return null;

    return (
      <div
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          maxWidth: "360px",
          width: "100%",
          pointerEvents: "none",
        }}
      >
        {toasts.map((toast) => {
          let bg = "#1f2937";
          let border = "#374151";
          let icon = "ℹ️";

          if (toast.type === "success") {
            bg = "#064e3b";
            border = "#10b981";
            icon = "✓";
          } else if (toast.type === "error") {
            bg = "#7f1d1d";
            border = "#ef4444";
            icon = "⚠️";
          } else if (toast.type === "warning") {
            bg = "#78350f";
            border = "#f59e0b";
            icon = "⚡";
          }

          return (
            <div
              key={toast.id}
              style={{
                pointerEvents: "auto",
                background: bg,
                border: `1px solid ${border}`,
                color: "white",
                padding: "12px 16px",
                borderRadius: "8px",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
                fontSize: "14px",
                fontWeight: 500,
                animation: "toastSlideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "16px" }}>{icon}</span>
                <span>{toast.message}</span>
              </div>
              <button
                onClick={() => onDismiss(toast.id)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "rgba(255, 255, 255, 0.7)",
                  cursor: "pointer",
                  fontSize: "16px",
                  lineHeight: 1,
                  padding: "4px",
                }}
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
    );
  }
);
ToastContainer.displayName = "ToastContainer";
