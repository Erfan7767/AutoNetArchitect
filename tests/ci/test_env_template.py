"""Contract tests for the safe V1 environment template."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_TEMPLATE = PROJECT_ROOT / ".env.example"


def _env_text() -> str:
    """Return the example environment template."""
    return ENV_TEMPLATE.read_text(encoding="utf-8")


def test_env_template_contains_supported_local_v1_settings() -> None:
    """Ensure the template documents only useful local V1 process settings."""
    text = _env_text()
    expected = {
        "AUTONET_API_ROOT=./runtime-data/api",
        "AUTONET_API_HOST=127.0.0.1",
        "AUTONET_API_PORT=8000",
        "AUTONET_API_URL=http://127.0.0.1:8000",
        "PYTHONPATH=.",
        "AUTONET_RUNTIME_MODE=local-single-user",
        "AUTONET_LOG_LEVEL=INFO",
    }
    for line in expected:
        assert line in text


def test_env_template_has_no_operational_secret_or_fake_feature_assignments() -> None:
    """Ensure unsupported secret, database, transport, feature, and cache keys are absent as assignments."""
    text = _env_text()
    unsupported_keys = (
        "AUTONET_DATABASE_PATH=",
        "AUTONET_SECURITY_VAULT_PATH=",
        "AUTONET_API_JWT_SECRET_KEY=",
        "AUTONET_API_CORS_ORIGINS=",
        "AUTONET_SSH_CONNECT_TIMEOUT=",
        "AUTONET_SSH_COMMAND_TIMEOUT=",
        "AUTONET_SSH_MAX_CONCURRENT_SESSIONS=",
        "AUTONET_FEATURES_ENABLE_",
        "AUTONET_CACHE_BACKEND=",
        "AUTONET_CACHE_MAX_SIZE_MB=",
    )
    for key in unsupported_keys:
        assert key not in text
    assert "CHANGE_ME" not in text
    assert "-----BEGIN" not in text


def test_env_template_explicitly_declares_unsupported_boundary() -> None:
    """Ensure the template explains why omitted variables must not be assumed active."""
    text = _env_text()
    assert "intentionally not present" in text
    assert "Do not assume" in text
