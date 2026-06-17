"""Module runner for the InsureFlow chatbot service."""

from __future__ import annotations

import uvicorn

from chat_bot.config import get_chat_bot_settings

APP_IMPORT = "chat_bot.app:app"


def main() -> None:
    """Run the chatbot FastAPI app with the configured host and port."""

    settings = get_chat_bot_settings()
    uvicorn.run(
        APP_IMPORT,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
