"""Virtual validation coordination with explicit fidelity and evidence matching."""

from __future__ import annotations

from collections.abc import Callable

from .models import VirtualTestResult

VirtualTestAdapter = Callable[[str, str, str], VirtualTestResult]


class VirtualValidationCoordinator:
    """Runs an injected virtual test adapter and rejects mismatched evidence records."""

    def __init__(self, adapter: VirtualTestAdapter) -> None:
        """Create a coordinator around an explicit lab, twin, or candidate-validation adapter."""

        self._adapter = adapter

    def validate(self, artifact_hash: str, target_facts_hash: str, scope_hash: str) -> VirtualTestResult:
        """Run validation and require the resulting evidence to match the requested inputs exactly."""

        result = self._adapter(artifact_hash, target_facts_hash, scope_hash)
        if result.artifact_hash != artifact_hash:
            raise ValueError("Virtual-test result artifact hash does not match the requested artifact.")
        if result.target_facts_hash != target_facts_hash:
            raise ValueError("Virtual-test result target facts do not match the requested target.")
        if result.scope_hash != scope_hash:
            raise ValueError("Virtual-test result scope does not match the requested scope.")
        return result
