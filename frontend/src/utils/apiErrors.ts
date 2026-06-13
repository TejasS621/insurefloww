import { ApiError, type ApiErrorItem, type FieldErrorMap } from "../services/api/types";

function mapFieldErrors(errors: any[]): FieldErrorMap {
  const fieldErrors: FieldErrorMap = {};
  if (!Array.isArray(errors)) return fieldErrors;

  errors.forEach((error, index) => {
    if (error && Array.isArray(error.loc)) {
      const pathSegments = error.loc.filter((segment: any) => segment !== "body");
      const fieldPath = pathSegments.join(".");
      fieldErrors[fieldPath] = error.msg ?? error.detail ?? "Invalid value.";

      const lastSegment = pathSegments[pathSegments.length - 1];
      if (lastSegment && typeof lastSegment === "string") {
        fieldErrors[lastSegment] = error.msg ?? error.detail ?? "Invalid value.";
      }
    } else if (error && error.type && (error.detail || error.msg)) {
      const fieldKey = error.type.includes(".") ? error.type : `field_${index}`;
      fieldErrors[fieldKey] = error.detail ?? error.msg;
    }
  });

  return fieldErrors;
}

/**
 * normalizeApiError converts unknown thrown values into a typed API error.
 * Screens use the normalized shape for inline validation and retry messaging.
 */
export function normalizeApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return new ApiError(
        "You don't have permission for this action.",
        error.status,
        error.code,
        error.errors,
        error.fieldErrors,
      );
    }
    if (error.status === 429) {
      return new ApiError(
        getTooManyRequestsMessage(error),
        error.status,
        error.code,
        error.errors,
        error.fieldErrors,
      );
    }
    return error;
  }
  return new ApiError(
    "An unexpected error occurred. Please try again.",
    500,
    "unknown_error",
  );
}

export function buildApiError(
  status: number,
  message: string,
  errors: any[] = [],
): ApiError {
  const finalMessage = status === 403 ? "You don't have permission for this action." : message;
  const fieldErrors = status === 422 ? mapFieldErrors(errors) : {};
  return new ApiError(finalMessage, status, errors[0]?.type ?? "api_error", errors, fieldErrors);
}

export function getTooManyRequestsMessage(error: ApiError): string {
  const retryDetail = error.errors.find((item) => item.type === "retry_after" || item.type === "retry");
  if (retryDetail) {
    return `Too many requests. Try again in ${retryDetail.detail}s.`;
  }
  const match = error.message.match(/(\d+)\s*(?:seconds|s)/i);
  if (match && match[1]) {
    return `Too many requests. Try again in ${match[1]}s.`;
  }
  return error.message || "Too many requests. Try again in a few seconds.";
}
