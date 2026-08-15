"""Contract tests for the containerized pytest Compose service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.test.yml"


def _compose() -> dict[str, Any]:
    """Load the test Compose document as a mapping."""
    value = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_test_service_uses_dev_image_and_full_pytest_command() -> None:
    """Ensure the test container runs all discovered test families with coverage."""
    service = _compose()["services"]["test"]
    assert service["build"]["dockerfile"] == "Dockerfile.dev"
    command = service["command"]
    assert command[:4] == ["python", "-m", "pytest", "tests/"]
    assert "--cov=autonetarchitect" in command
    assert "--cov-config=coverage_config/.coveragerc" in command
    assert "--cov-report=xml:/tmp/coverage.xml" in command
    assert "-x" in command


def test_test_service_uses_read_only_source_and_writable_test_mounts() -> None:
    """Ensure source is protected while pytest cache and temporary output remain writable."""
    service = _compose()["services"]["test"]
    assert ".:/workspace:ro" in service["volumes"]
    assert "test_cache:/workspace/.pytest_cache" in service["volumes"]
    assert "test_tmp:/tmp" in service["volumes"]
    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]


def test_test_service_has_explicit_non_secret_test_environment() -> None:
    """Ensure test mode and coverage storage are explicit without fake database isolation claims."""
    service = _compose()["services"]["test"]
    environment = service["environment"]
    assert environment["PYTHONPATH"] == "/workspace"
    assert environment["AUTONET_RUNTIME_MODE"] == "test"
    assert environment["AUTONET_LOG_LEVEL"] == "WARNING"
    assert environment["COVERAGE_FILE"] == "/tmp/.coverage"
    assert "AUTONET_DATABASE_PATH" not in environment


def test_test_service_declares_named_ephemeral_volumes() -> None:
    """Ensure cache and temporary output volumes have stable Compose names."""
    volumes = _compose()["volumes"]
    assert volumes["test_cache"]["name"] == "autonetarchitect_test_cache"
    assert volumes["test_tmp"]["name"] == "autonetarchitect_test_tmp"
