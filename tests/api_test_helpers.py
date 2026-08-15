"""Shared helpers for API custom-runner tests."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from fastapi.testclient import TestClient

from api.server import APIContext, APISettings, create_app


class APITestHarness:
    """Temporary API context and TestClient lifecycle helper."""

    def __init__(self) -> None:
        """Create a temporary root and local API context."""
        self._temporary = TemporaryDirectory()
        root = Path(self._temporary.name)
        settings = APISettings.from_root(root, jwt_secret=b"a" * 32, rate_limit=100, rate_window_seconds=60)
        self.context = APIContext(settings)
        self.context.auth_manager.create_user("admin", "strong-password-123", ("admin",))
        self.context.auth_manager.create_user("viewer", "viewer-password-123", ("viewer",))
        self.client = TestClient(create_app(self.context))

    def close(self) -> None:
        """Close the temporary root."""
        self._temporary.cleanup()

    def login(self, username: str = "admin", password: str = "strong-password-123") -> str:
        """Return a bearer token for one local user."""
        response = self.client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200, response.text
        return str(response.json()["access_token"])

    def auth_headers(self, username: str = "admin", password: str = "strong-password-123") -> dict[str, str]:
        """Return Authorization header mapping."""
        return {"Authorization": f"Bearer {self.login(username, password)}"}
