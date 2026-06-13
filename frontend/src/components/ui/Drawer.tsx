import type { ReactNode } from "react";

interface DrawerProps {
  title: string;
  children: ReactNode;
  width?: "default" | "wide";
}

/**
 * Drawer renders right-side record detail panels for admin tables and tickets.
 * It keeps detail inspection inline rather than navigating away from list pages.
 */
export function Drawer({ title, children, width = "default" }: DrawerProps) {
  return (
    <div className="if-overlay if-overlay-right">
      <aside className={`if-drawer ${width === "wide" ? "if-drawer-wide" : ""}`}>
        <h2 className="if-modal-title">{title}</h2>
        {children}
      </aside>
    </div>
  );
}
