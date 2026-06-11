"""FastAPI application bootstrap for the main backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.main_backend.app.commons.config import settings
from backend.main_backend.app.core.database.database import (
    close_mongo_connection,
    connect_to_mongo,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application startup and shutdown resources."""
    logger.info("Starting %s", settings.app_name)
    await connect_to_mongo()
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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return a simple health response for local development."""
    return {"status": "ok", "service": "main_backend"}

