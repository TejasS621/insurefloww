import { useEffect, useState } from "react";

/**
 * useDebouncedValue delays propagating a value until the delay passes.
 * Admin search filters use it to avoid firing a request on every keypress.
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedValue(value), delayMs);
    return () => window.clearTimeout(timeout);
  }, [delayMs, value]);

  return debouncedValue;
}
