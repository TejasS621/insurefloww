"""FastAPI application bootstrap for the provider backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.provider_backend.app.commons.config import settings
from backend.provider_backend.app.core.apis.routes import (
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
from backend.provider_backend.app.core.database.database import (
    close_mongo_connection,
    connect_to_mongo,
)
from backend.provider_backend.app.core.services.broker_service import broker_service
from backend.provider_backend.app.core.services.catalog_seeder import seed_catalog
from backend.provider_backend.app.core.services.service_exceptions import ServiceError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application startup and shutdown resources."""
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
    """Return a structured validation error response."""
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
    """Convert service-layer errors into structured API responses."""
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
    """Prevent raw exceptions from leaking to clients."""
    logger.exception("Unhandled error in provider backend", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected server error occurred.",
            "errors": [{"type": "server_error", "detail": str(exc)}],
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
