import { authStore } from "../../store/authStore";
import { buildApiError } from "../../utils/apiErrors";
import { API_BASE_URL } from "./config";
import type { ApiFailureResponse, ApiResponse } from "./types";

interface RequestOptions extends Omit<RequestInit, "body"> {
  admin?: boolean;
  body?: unknown;
}

function getHeaders(options: RequestOptions): Headers {
  const headers = new Headers(options.headers ?? {});
  headers.set("Accept", "application/json");

  if (options.body instanceof Blob) {
    return headers;
  }

  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const { customerToken, adminToken } = authStore.getState();

  if (options.admin) {
    if (adminToken) {
      headers.set("Authorization", `Bearer ${adminToken}`);
      headers.set("X-Admin-Token", adminToken);
    }
  } else if (customerToken) {
    headers.set("Authorization", `Bearer ${customerToken}`);
  }

  return headers;
}

/**
 * apiRequest wraps fetch with shared auth headers, credentials, and error parsing.
 * It also clears session state on 401 so screens can send users back to login.
 */
export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      credentials: "include",
      headers: getHeaders(options),
    });
  } catch {
    throw buildApiError(
      503,
      "Unable to reach the backend service. Please make sure the main and provider backends are running.",
      [{ type: "network_error", detail: "Backend service is unreachable." }],
    );
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  if (!response.ok) {
    const payload = isJson ? ((await response.json()) as ApiFailureResponse | ApiResponse<never>) : null;
    const message = payload?.message ?? "Request failed.";
    const errors = payload && "errors" in payload ? payload.errors : [];

    if (response.status === 401) {
      authStore.clear(options.admin ? "admin" : "customer");
    }

    throw buildApiError(response.status, message, errors);
  }

  if (!isJson) {
    return (await response.blob()) as T;
  }

  const payload = (await response.json()) as ApiResponse<T>;
  if (!payload.success) {
    throw buildApiError(response.status, payload.message, payload.errors);
  }
  return payload.data;
}
