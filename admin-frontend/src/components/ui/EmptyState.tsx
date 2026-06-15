import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

/**
 * EmptyState gives future screens a shared no-data presentation.
 * The illustration stays geometric so it fits the platform visual system.
 */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="if-empty-state">
      <svg
        aria-hidden="true"
        fill="none"
        viewBox="0 0 240 160"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect x="32" y="28" width="176" height="104" rx="18" fill="rgba(124, 58, 237, 0.08)" />
        <rect x="50" y="44" width="140" height="18" rx="9" fill="rgba(124, 58, 237, 0.12)" />
        <rect x="50" y="74" width="82" height="12" rx="6" fill="rgba(6, 182, 212, 0.12)" />
        <rect x="50" y="94" width="122" height="12" rx="6" fill="rgba(6, 182, 212, 0.12)" />
        <circle cx="187" cy="91" r="26" fill="url(#if-empty-gradient)" />
        <path
          d="M178 91L185 98L199 84"
          stroke="white"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="5"
        />
        <defs>
          <linearGradient id="if-empty-gradient" x1="161" x2="211" y1="71" y2="116">
            <stop stopColor="#7C3AED" />
            <stop offset="0.62" stopColor="#4C1D95" />
            <stop offset="1" stopColor="#06B6D4" />
          </linearGradient>
        </defs>
      </svg>
      <h3>{title}</h3>
      <p>{description}</p>
      {action ? <div className="if-empty-state-action">{action}</div> : null}
    </div>
  );
}
