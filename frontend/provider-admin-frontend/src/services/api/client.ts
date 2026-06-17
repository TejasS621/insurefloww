import { authStore } from "../../store/authStore";
import { buildApiError } from "../../utils/apiErrors";
import { MAIN_API_BASE_URL, PROVIDER_API_BASE_URL } from "./config";
import type { ApiFailureResponse, ApiResponse } from "./types";

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

function getHeaders(options: RequestOptions): Headers {
  const headers = new Headers(options.headers ?? {});
  headers.set("Accept", "application/json");

  if (!(options.body instanceof Blob) && options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const { providerAdminToken } = authStore.getState();
  if (providerAdminToken) {
    headers.set("Authorization", `Bearer ${providerAdminToken}`);
  }

  return headers;
}

async function executeApiRequest<T>(
  baseUrl: string,
  path: string,
  options: RequestOptions,
  networkMessage: string,
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...options,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      headers: getHeaders(options),
    });
  } catch {
    throw buildApiError(
      503,
      networkMessage,
      [{ type: "network_error", detail: networkMessage }],
    );
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  if (!response.ok) {
    const payload = isJson
      ? ((await response.json()) as ApiFailureResponse | ApiResponse<never>)
      : null;
    const message = payload?.message ?? "Provider request failed.";
    const errors = payload && "errors" in payload ? payload.errors : [];

    if (response.status === 401) {
      authStore.clear();
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

export function providerApiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  return executeApiRequest(
    PROVIDER_API_BASE_URL,
    path,
    options,
    "Unable to reach the provider backend. Please make sure the provider backend is running.",
  );
}

export function mainApiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  return executeApiRequest(
    MAIN_API_BASE_URL,
    path,
    options,
    "Unable to reach the main backend. Please make sure the main backend is running.",
  );
}
