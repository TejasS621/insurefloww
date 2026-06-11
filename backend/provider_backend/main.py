"""Development entrypoint for the provider backend service."""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn


root_dir = str(Path(__file__).resolve().parents[2])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.provider_backend.app.commons.config import settings


APP_IMPORT = "backend.provider_backend.app.core.apis.api:app"


if __name__ == "__main__":
    uvicorn.run(
        APP_IMPORT,
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )
