import { ApiError, type ApiErrorItem, type FieldErrorMap } from "../services/api/types";

function mapFieldErrors(errors: ApiErrorItem[]): FieldErrorMap {
  return errors.reduce<FieldErrorMap>((accumulator, error, index) => {
    const fieldKey = error.type.includes(".") ? error.type : `field_${index}`;
    accumulator[fieldKey] = error.detail;
    return accumulator;
  }, {});
}

/**
 * normalizeApiError converts unknown thrown values into a typed API error.
 * Screens use the normalized shape for inline validation and retry messaging.
 */
export function normalizeApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
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
  errors: ApiErrorItem[] = [],
): ApiError {
  const fieldErrors = status === 422 ? mapFieldErrors(errors) : {};
  return new ApiError(message, status, errors[0]?.type ?? "api_error", errors, fieldErrors);
}

export function getTooManyRequestsMessage(error: ApiError): string {
  const retryDetail = error.errors.find((item) => item.type === "retry_after");
  return retryDetail
    ? `Too many requests. Try again in ${retryDetail.detail}.`
    : "Too many requests. Try again in a few seconds.";
}
