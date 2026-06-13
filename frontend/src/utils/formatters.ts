/**
 * formatCurrencyINR renders all platform amounts in Indian Rupee format.
 * Shared formatting avoids screen-level inconsistencies in money display.
 */
export function formatCurrencyINR(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}
