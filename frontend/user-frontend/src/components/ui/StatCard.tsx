type StatVariant =
  | "primary"
  | "navy"
  | "coverage"
  | "policies"
  | "renewal"
  | "tickets"
  | "stat-1"
  | "stat-2"
  | "stat-3"
  | "stat-4";

interface StatCardProps {
  label: string;
  value: string;
  variant?: StatVariant;
}

/**
 * StatCard is a shell-level metric card for dashboards and summaries.
 * It exposes only the value and label so page code stays lean.
 */
export function StatCard({ label, value, variant = "primary" }: StatCardProps) {
  const getVariantClass = () => {
    switch (variant) {
      case "coverage":
      case "stat-1":
        return "if-stat-card-coverage";
      case "policies":
      case "stat-2":
        return "if-stat-card-policies";
      case "renewal":
      case "stat-3":
        return "if-stat-card-renewal";
      case "tickets":
      case "stat-4":
        return "if-stat-card-tickets";
      case "navy":
        return "if-stat-card-alt";
      default:
        return "";
    }
  };

  return (
    <article className={`if-stat-card ${getVariantClass()}`}>
      <p className="if-stat-label">{label}</p>
      <p className="if-stat-value">{value}</p>
    </article>
  );
}
