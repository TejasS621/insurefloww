export interface ApiErrorItem {
  type: string;
  detail: string;
}

export interface ApiSuccessResponse<T> {
  success: true;
  message: string;
  data: T;
}

export interface ApiFailureResponse {
  success: false;
  message: string;
  errors: ApiErrorItem[];
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiFailureResponse;

export interface FieldErrorMap {
  [key: string]: string;
}

export class ApiError extends Error {
  status: number;
  code: string;
  errors: ApiErrorItem[];
  fieldErrors: FieldErrorMap;

  constructor(
    message: string,
    status: number,
    code = "api_error",
    errors: ApiErrorItem[] = [],
    fieldErrors: FieldErrorMap = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.errors = errors;
    this.fieldErrors = fieldErrors;
  }
}
