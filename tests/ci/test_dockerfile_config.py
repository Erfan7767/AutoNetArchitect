"""Contract tests for the V1 release Dockerfile."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = PROJECT_ROOT / "Dockerfile"


def _dockerfile_text() -> str:
    """Return the release Dockerfile text."""
    return DOCKERFILE.read_text(encoding="utf-8")


def test_dockerfile_uses_separate_builder_and_runtime_stages() -> None:
    """Ensure native build dependencies are isolated from the runtime stage."""
    text = _dockerfile_text()
    assert "FROM python:3.11-slim AS builder" in text
    assert "FROM python:3.11-slim AS runtime" in text
    assert "gcc" in text
    assert "libffi-dev" in text
    assert "COPY --from=builder /install /usr/local" in text


def test_dockerfile_copies_complete_v1_runtime_boundaries() -> None:
    """Ensure API, CLI, package, and non-packaged runtime data are present."""
    text = _dockerfile_text()
    for path in ("api", "cli", "autonetarchitect", "data", "auth", "audit", "orchestrators"):
        assert f"/build/{path}" in text
    assert "/build/constants.py" in text
    assert "/build/exceptions.py" in text
    assert "/build/schema_version.py" in text


def test_dockerfile_enforces_non_root_and_local_state_boundaries() -> None:
    """Ensure the runtime uses a dedicated user and writable state volume."""
    text = _dockerfile_text()
    assert "groupadd --system --gid 10001 autonet" in text
    assert "useradd --system --uid 10001" in text
    assert "USER autonet" in text
    assert 'VOLUME ["/var/lib/autonetarchitect"]' in text
    assert "AUTONET_API_ROOT=/var/lib/autonetarchitect" in text
    assert "chown -R autonet:autonet" in text


def test_dockerfile_preserves_api_entrypoint_and_health_contract() -> None:
    """Ensure the default container serves the implemented API liveness route."""
    text = _dockerfile_text()
    assert 'CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]' in text
    assert "EXPOSE 8000" in text
    assert "HEALTHCHECK" in text
    assert "/api/v1/health/live" in text
    assert "127.0.0.1:8000" in text


def test_dockerfile_installs_declared_runtime_native_dependency() -> None:
    """Ensure graphviz requested by the supplied baseline is installed at runtime."""
    text = _dockerfile_text()
    assert "apt-get install -y --no-install-recommends" in text
    assert "graphviz" in text
