"""
Bootstrap the provider backend FastAPI application.

Args:
    None: This module defines the FastAPI app instance, middleware, router
    registration, and shared exception handlers for the provider backend.

Returns:
    None: Importing this module exposes the configured FastAPI application.

Raises:
    HTTPException: Route-level exceptions are normalized through registered
    handlers before being returned to API clients.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.provider_backend.commons.config import settings
from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.apis.routes import (
    auth_router,
    health_router,
    mock_payment_router,
    payment_router,
    policy_router,
    provider_router,
    quote_router,
    sync_router,
    webhook_router,
)
from backend.provider_backend.core.database.database import (
    close_mongo_connection,
    connect_to_mongo,
)
from backend.provider_backend.core.services.broker_service import broker_service
from backend.provider_backend.core.services.catalog_seeder import seed_catalog
from backend.provider_backend.core.services.service_exceptions import ServiceError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Manage startup and shutdown resources for the provider backend.

    Args:
        _: FastAPI application instance supplied by the lifespan hook.

    Returns:
        AsyncIterator[None]: Control back to FastAPI while the app is running.

    Raises:
        Exception: Propagates startup or shutdown failures so the process does
        not continue in a partially initialized state.
    """
    logger.info("Starting %s", settings.app_name)
    engine = await connect_to_mongo()
    await broker_service.ensure_integration_broker(engine)
    await seed_catalog(engine)
    try:
        yield
    finally:
        await close_mongo_connection()
        logger.info("Stopped %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_origin_regex=settings.cors_allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Convert request validation failures into a consistent API response.

    Args:
        _: Request instance supplied by FastAPI.
        exc: Validation exception raised while parsing the incoming request.

    Returns:
        JSONResponse: Structured validation error payload for the client.

    Raises:
        RequestValidationError: Captured here and translated into JSON rather
        than being exposed as a raw framework error.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Request validation failed.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(ServiceError)
async def service_exception_handler(_: Request, exc: ServiceError) -> JSONResponse:
    """
    Convert service-layer errors into structured API responses.

    Args:
        _: Request instance supplied by FastAPI.
        exc: Domain-level service exception raised by provider services.

    Returns:
        JSONResponse: Structured error payload using the mapped status code.

    Raises:
        ServiceError: Captured here and converted into a safe API response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "errors": [{"type": exc.code, "detail": exc.message}],
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """
    Prevent raw unexpected exceptions from leaking to clients.

    Args:
        _: Request instance supplied by FastAPI.
        exc: Unexpected exception raised during request handling.

    Returns:
        JSONResponse: Generic internal server error payload.

    Raises:
        Exception: Logged here before being converted into a safe response.
    """
    logger.exception("Unhandled error in provider backend", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected server error occurred.",
            "errors": [{"type": "server_error", "detail": "Internal server error"}],
        },
    )


app.include_router(health_router)
app.include_router(mock_payment_router)
app.include_router(auth_router)
app.include_router(provider_router)
app.include_router(quote_router)
app.include_router(payment_router)
app.include_router(policy_router)
app.include_router(sync_router)
app.include_router(webhook_router)
