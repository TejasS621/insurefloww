"""Development entrypoint for the main backend service."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


root_dir = str(Path(__file__).resolve().parents[2])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


APP_IMPORT = "backend.main_backend.app.core.apis.api:app"
HOST = os.getenv("MAIN_BACKEND_HOST", "127.0.0.1")
PORT = int(os.getenv("MAIN_BACKEND_PORT", "8000"))


if __name__ == "__main__":
    uvicorn.run(APP_IMPORT, host=HOST, port=PORT, reload=True)
