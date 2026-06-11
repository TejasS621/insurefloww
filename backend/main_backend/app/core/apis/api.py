"""FastAPI application bootstrap for the main backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.main_backend.app.core.apis.routes import (
    admin_router,
    application_router,
    auth_router,
    health_router,
    payment_router,
    policy_router,
    provider_sync_router,
    quote_router,
    ticket_router,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application startup and shutdown hooks."""
    logger.info("Starting main backend service")
    yield
    logger.info("Stopping main backend service")


app = FastAPI(
    title="InsureFlow Main Backend",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Prevent raw exceptions from leaking to clients."""
    logger.exception("Unhandled error in main backend", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected server error occurred.",
            "errors": [{"type": "server_error", "detail": str(exc)}],
        },
    )


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(application_router)
app.include_router(quote_router)
app.include_router(payment_router)
app.include_router(policy_router)
app.include_router(ticket_router)
app.include_router(admin_router)
app.include_router(provider_sync_router)
