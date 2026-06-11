"""Service-layer exception types for the provider backend."""

from __future__ import annotations


class ServiceError(Exception):
    """Base error raised by provider service-layer operations."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "service_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ValidationServiceError(ServiceError):
    """Raised when business validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error", status_code=400)


class AuthenticationServiceError(ServiceError):
    """Raised when provider admin authentication fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="authentication_error", status_code=401)


class NotFoundServiceError(ServiceError):
    """Raised when a required record cannot be located."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found", status_code=404)


class ConflictServiceError(ServiceError):
    """Raised when an operation conflicts with existing state."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="conflict", status_code=409)


class IntegrationServiceError(ServiceError):
    """Raised when downstream integration steps cannot be completed."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="integration_error", status_code=502)

