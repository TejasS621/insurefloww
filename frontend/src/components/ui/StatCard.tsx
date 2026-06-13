interface StatCardProps {
  label: string;
  value: string;
  variant?: "primary" | "navy";
}

/**
 * StatCard is a shell-level metric card for dashboards and summaries.
 * It exposes only the value and label so page code stays lean.
 */
export function StatCard({ label, value, variant = "primary" }: StatCardProps) {
  return (
    <article className={`if-stat-card ${variant === "navy" ? "if-stat-card-alt" : ""}`}>
      <p className="if-stat-label">{label}</p>
      <p className="if-stat-value">{value}</p>
    </article>
  );
}
