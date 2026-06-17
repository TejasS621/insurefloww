import type { ReactNode } from "react";

type StatusTone = "issued" | "pending" | "failed" | "processing" | "cancelled" | "admin";

interface StatusBadgeProps {
  status: StatusTone;
  children: ReactNode;
}

/**
 * StatusBadge standardizes pill treatments for workflow states.
 * Shared usage keeps admin and customer status language visually aligned.
 */
export function StatusBadge({ status, children }: StatusBadgeProps) {
  return <span className={`if-badge if-badge-${status}`}>{children}</span>;
}
