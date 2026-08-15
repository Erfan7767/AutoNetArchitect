"""Contract tests for the local API/UI Docker Compose topology."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"


def _compose() -> dict[str, Any]:
    """Load the Compose document as a mapping."""
    value = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_compose_declares_api_and_optional_ui_services() -> None:
    """Ensure the requested API/UI topology is represented explicitly."""
    document = _compose()
    services = document.get("services")
    assert isinstance(services, dict)
    assert set(services) == {"api", "ui"}
    assert services["api"]["image"] == "autonetarchitect:0.1.0"
    assert services["ui"]["image"] == "autonetarchitect:ui"


def test_api_service_matches_implemented_health_and_state_contract() -> None:
    """Ensure API command, state root, and liveness route match the implementation."""
    api = _compose()["services"]["api"]
    assert api["command"] == ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
    assert api["environment"]["AUTONET_API_ROOT"] == "/var/lib/autonetarchitect"
    assert api["volumes"] == ["autonet_state:/var/lib/autonetarchitect"]
    assert "/api/v1/health/live" in api["healthcheck"]["test"][-1]
    assert "AUTONET_DATABASE_PATH" not in api["environment"]


def test_compose_keeps_services_local_and_hardened() -> None:
    """Ensure ports bind to loopback and both services use container hardening."""
    services = _compose()["services"]
    assert services["api"]["ports"] == ["127.0.0.1:8000:8000"]
    assert services["ui"]["ports"] == ["127.0.0.1:8501:8501"]
    for service in services.values():
        assert service["read_only"] is True
        assert service["cap_drop"] == ["ALL"]
        assert service["security_opt"] == ["no-new-privileges:true"]
        assert "/tmp" in service["tmpfs"]


def test_ui_service_uses_optional_profile_and_api_dependency() -> None:
    """Ensure Streamlit is isolated to the UI build and waits for API liveness."""
    ui = _compose()["services"]["ui"]
    assert ui["build"]["args"]["INSTALL_EXTRAS"] == "optional"
    assert ui["command"][:3] == ["streamlit", "run", "ui/streamlit_app.py"]
    assert ui["environment"]["AUTONET_API_URL"] == "http://api:8000"
    assert ui["environment"]["STREAMLIT_CONFIG_DIR"] == "/tmp/.streamlit"
    assert ui["environment"]["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] == "false"
    assert ui["depends_on"]["api"]["condition"] == "service_healthy"
    assert "/_stcore/health" in ui["healthcheck"]["test"][-1]


def test_streamlit_adapter_is_framework_adapter_only() -> None:
    """Ensure the optional adapter delegates to API liveness and declares read-only scope."""
    adapter = (PROJECT_ROOT / "ui" / "streamlit_app.py").read_text(encoding="utf-8")
    assert "/api/v1/health/live" in adapter
    assert "read_only" in adapter
    assert "local-single-user" in adapter
    assert "UIController" not in adapter
    assert "Orchestrator" not in adapter
