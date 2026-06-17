export const PROVIDER_API_BASE_URL =
  import.meta.env.VITE_PROVIDER_BACKEND_API_BASE_URL?.trim() ||
  "http://127.0.0.1:8001/api/v1";

export const MAIN_API_BASE_URL =
  import.meta.env.VITE_MAIN_BACKEND_API_BASE_URL?.trim() ||
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  "http://127.0.0.1:8000/api/v1";
