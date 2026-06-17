"""Fixtures and configuration for chatbot tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from chat_bot.app import app


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient bound to the FastAPI application."""
    return TestClient(app)
