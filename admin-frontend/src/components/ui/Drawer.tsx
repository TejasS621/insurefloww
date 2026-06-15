import { X } from "lucide-react";
import type { ReactNode } from "react";

interface DrawerProps {
  title: string;
  children: ReactNode;
  width?: "default" | "wide";
  onClose?: () => void;
}

/**
 * Drawer renders right-side record detail panels for admin tables and tickets.
 * It keeps detail inspection inline rather than navigating away from list pages.
 */
export function Drawer({ title, children, width = "default", onClose }: DrawerProps) {
  return (
    <div className="if-overlay if-overlay-right" onClick={onClose}>
      <aside
        className={`if-drawer ${width === "wide" ? "if-drawer-wide" : ""}`}
        onClick={(event) => event.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-6)" }}>
          <h2 className="if-modal-title" style={{ margin: 0 }}>{title}</h2>
          {onClose ? (
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--if-text-2)",
                cursor: "pointer",
                padding: "4px",
                display: "flex",
                alignItems: "center",
              }}
              type="button"
              aria-label="Close drawer"
            >
              <X size={20} />
            </button>
          ) : null}
        </div>
        {children}
      </aside>
    </div>
  );
}
