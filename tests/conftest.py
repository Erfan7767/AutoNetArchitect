"""Shared final-test fixtures and helper contracts.

The project uses custom importlib runners rather than pytest; these helpers remain
plain Python so they are reusable from every test family.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator

from persistence.project_persistence import ProjectPersistence


TEST_ROOT = Path(__file__).resolve().parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"


def load_json_fixture(relative_path: str) -> dict[str, Any]:
    """Load one deterministic JSON fixture from the final-test fixture root."""
    target = FIXTURE_ROOT / relative_path
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"fixture must be a JSON object: {relative_path}")
    return payload


@contextmanager
def temporary_project_store() -> Iterator[ProjectPersistence]:
    """Yield isolated local-first persistence for one test scenario."""
    with TemporaryDirectory(prefix="autonet-final-test-") as temporary:
        yield ProjectPersistence(Path(temporary) / "projects")


def assert_secret_safe(value: Any) -> None:
    """Reject raw secret-like values in serialized test outputs."""
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).lower()
    forbidden = ("strong-password", "private_key", "raw-secret", "super-secret", "enable-password")
    for marker in forbidden:
        if marker in serialized:
            raise AssertionError(f"raw secret marker found in output: {marker}")


def assert_production_readiness_boundaries(payload: dict[str, Any]) -> None:
    """Assert explicit readiness boundaries rather than broad success claims."""
    rules = load_json_fixture("expected_outputs/pipeline_expectations.json")["production_readiness_rules"]
    if rules["deployment_requires_backup"] and payload.get("real_execution") is True:
        if not payload.get("backup_reference"):
            raise AssertionError("real execution without backup must not be considered ready")
    if rules["formal_verification_status_must_be_explicit"] and "proof_status" in payload and not payload["proof_status"]:
        raise AssertionError("proof status must be explicit when verification is included")
