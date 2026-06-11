"""MongoDB connection management for the provider backend."""

from __future__ import annotations

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from backend.provider_backend.app.commons.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_engine: Optional[AIOEngine] = None


async def connect_to_mongo() -> AIOEngine:
    """Create and validate the MongoDB connection for the provider backend."""
    global _client, _engine

    if _client is not None and _engine is not None:
        return _engine

    try:
        logger.info("Connecting provider backend to MongoDB at %s", settings.mongodb_url)
        _client = AsyncIOMotorClient(settings.mongodb_url)
        await _client.admin.command("ping")
        _engine = AIOEngine(client=_client, database=settings.database_name)
        logger.info(
            "Provider backend connected to MongoDB database '%s'",
            settings.database_name,
        )
        return _engine
    except Exception as exc:
        logger.exception("Failed to connect provider backend to MongoDB", exc_info=exc)
        _client = None
        _engine = None
        raise RuntimeError(
            f"Unable to connect provider backend to MongoDB database '{settings.database_name}'."
        ) from exc


async def close_mongo_connection() -> None:
    """Close the active MongoDB client if one exists."""
    global _client, _engine

    if _client is None:
        return

    logger.info("Closing provider backend MongoDB connection")
    _client.close()
    _client = None
    _engine = None


def get_engine() -> AIOEngine:
    """Return the active ODMantic engine."""
    if _engine is None:
        raise RuntimeError(
            "MongoDB engine is not initialized. Call connect_to_mongo() during startup first."
        )
    return _engine


async def get_database() -> AIOEngine:
    """FastAPI dependency that provides the active ODMantic engine."""
    return get_engine()
