"""Contract tests for import-safe core boundaries and package module discovery."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Final

import pytest

PACKAGE_NAME: Final[str] = "autonetarchitect"
CORE_MODULES: Final[tuple[str, ...]] = (
    "autonetarchitect",
    "autonetarchitect.cli.main",
    "api.server",
    "cli.main",
    "orchestrators.master_orchestrator",
    "orchestrators.design_orchestrator",
    "orchestrators.deployment_orchestrator",
    "orchestrators.operations_orchestrator",
    "persistence.project_persistence",
    "source_of_truth.sot_manager",
    "auth.auth_manager",
    "audit.audit_trail",
    "secrets.secret_manager",
    "governance.signoff_policy",
    "supervised_mode.workflow_mode",
    "review_control.readiness_gate",
)


def find_all_modules() -> tuple[str, ...]:
    """Find the package and every recursively discoverable module below it."""
    package = importlib.import_module(PACKAGE_NAME)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        raise RuntimeError(f"{PACKAGE_NAME} is not a package with a discoverable path")
    discovered = {package.__name__}
    discovered.update(module_info.name for module_info in pkgutil.walk_packages(package_path, prefix=f"{PACKAGE_NAME}."))
    return tuple(sorted(discovered))


def test_core_modules_import_without_optional_integrations() -> None:
    """Verify that the core workflow imports do not require optional UI/rendering packages."""
    for module_name in CORE_MODULES:
        imported = importlib.import_module(module_name)
        assert imported is not None, module_name


@pytest.mark.parametrize("module_name", find_all_modules())
def test_module_imports(module_name: str) -> None:
    """Import every discoverable autonetarchitect module without an import-time error."""
    imported = importlib.import_module(module_name)
    assert imported is not None, module_name
