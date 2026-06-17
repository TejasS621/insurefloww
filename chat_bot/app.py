"""FastAPI application entrypoint for the InsureFlow chatbot service."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chat_bot.config import get_chat_bot_settings
from chat_bot.routers.chat_router import chat_router

settings = get_chat_bot_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    """Return a simple health payload for local checks and deployment probes."""

    return {"status": "ok"}
