from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


root_dir = str(Path(__file__).resolve().parents[2])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


APP_IMPORT = "backend.provider_backend.app.core.apis.api:app"
HOST = os.getenv("PROVIDER_BACKEND_HOST", "127.0.0.1")
PORT = int(os.getenv("PROVIDER_BACKEND_PORT", "8001"))


if __name__ == "__main__":
    uvicorn.run(APP_IMPORT, host=HOST, port=PORT, reload=True)
