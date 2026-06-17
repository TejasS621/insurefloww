export const API_BASE_URL =
  import.meta.env.VITE_MAIN_BACKEND_API_BASE_URL?.trim() ||
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  "http://127.0.0.1:8000/api/v1";

export const REQUEST_DEBOUNCE_MS = 400;
export const CUSTOMER_PAYMENT_POLL_INTERVAL_MS = 3000;
export const CUSTOMER_PAYMENT_POLL_LIMIT = 10;
export const POLICY_POLL_INTERVAL_MS = 5000;
export const POLICY_POLL_TIMEOUT_MS = 5 * 60 * 1000;
