interface SkeletonProps {
  width?: number | string;
  height?: number | string;
}

/**
 * Skeleton provides a shared shimmer placeholder for async UI.
 * Pages can reuse it for cards, tables, and list rows during fetches.
 */
export function Skeleton({ width = "100%", height = 20 }: SkeletonProps) {
  return <div className="if-skeleton" style={{ width, height }} />;
}
