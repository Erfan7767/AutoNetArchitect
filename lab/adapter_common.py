"""Shared implementation for provider-specific lab adapters."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Callable, Mapping

from .lab_manager import LabOperation, LabState, LabVerificationExecution


LabExecutor = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]


@dataclass
class BaseLabAdapter:
    """Common safe execution boundary for lab provider adapters."""

    provider_name: str
    executor: LabExecutor | None = None

    def _operation(self, operation: str, payload: Mapping[str, Any]) -> LabOperation:
        """Return preview, blocked, executed, or failed result for one operation."""
        payload_hash = self._hash(payload)
        if self._contains_inline_secret(payload):
            return LabOperation(self.provider_name, operation, LabState.BLOCKED_MISSING_HUMAN_DATA.value, "inline secret material is not accepted by the lab adapter", True, True, payload_hash, required_human_inputs=("secret_manager_reference",))
        if self.executor is None:
            return LabOperation(self.provider_name, operation, LabState.PREVIEW_ONLY.value, "provider driver is not configured; operation remains validation preview-only", True, True, payload_hash)
        try:
            result = dict(self.executor(operation, payload))
        except Exception:
            return LabOperation(self.provider_name, operation, LabState.FAILED.value, "provider driver failed without exposing runtime details", True, True, payload_hash)
        requested_state = str(result.get("state", LabState.EXECUTED.value))
        state = requested_state if requested_state in {item.value for item in LabState} else LabState.EXECUTED.value
        return LabOperation(self.provider_name, operation, state, str(result.get("detail", "provider driver returned an operation result")), True, True, payload_hash, tuple(str(item) for item in result.get("evidence_ids", ()) if item), tuple(str(item) for item in result.get("required_human_inputs", ()) if item), str(result.get("provider_reference", "")))

    def _verification(self, plan: Mapping[str, Any], payload: Mapping[str, Any]) -> LabVerificationExecution:
        """Execute or preview verification exactly once and return sanitized observations."""
        operation = "run_verification"
        payload_hash = self._hash(payload)
        if self._contains_inline_secret(payload):
            return LabVerificationExecution(LabOperation(self.provider_name, operation, LabState.BLOCKED_MISSING_HUMAN_DATA.value, "inline secret material is not accepted by the lab adapter", True, True, payload_hash, required_human_inputs=("secret_manager_reference",)))
        if self.executor is None:
            return LabVerificationExecution(LabOperation(self.provider_name, operation, LabState.PREVIEW_ONLY.value, "provider driver is not configured; verification remains preview-only", True, True, payload_hash))
        try:
            result = dict(self.executor(operation, payload))
        except Exception:
            return LabVerificationExecution(LabOperation(self.provider_name, operation, LabState.FAILED.value, "provider verification failed without exposing runtime details", True, True, payload_hash))
        requested_state = str(result.get("state", LabState.EXECUTED.value))
        state = requested_state if requested_state in {item.value for item in LabState} else LabState.EXECUTED.value
        operation_result = LabOperation(self.provider_name, operation, state, str(result.get("detail", "provider verification returned an operation result")), True, True, payload_hash, tuple(str(item) for item in result.get("evidence_ids", ()) if item), tuple(str(item) for item in result.get("required_human_inputs", ()) if item), str(result.get("provider_reference", "")))
        observations = result.get("observations", {})
        raw_outputs = result.get("raw_outputs", {})
        return LabVerificationExecution(operation_result, dict(observations) if isinstance(observations, Mapping) else {}, {str(key): self.sanitize_text(str(value)) for key, value in raw_outputs.items()} if isinstance(raw_outputs, Mapping) else {})

    @staticmethod
    def _hash(payload: Mapping[str, Any]) -> str:
        """Create a deterministic payload hash for audit lineage."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def _contains_inline_secret(value: Any, key: str = "") -> bool:
        """Reject likely secret values while allowing secret:// references."""
        sensitive = ("password", "passwd", "secret", "token", "private_key", "api_key", "community")
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                lowered = str(child_key).lower()
                if "reference" in lowered and isinstance(child, (list, tuple, set)):
                    if all(not isinstance(item, str) or item.startswith("secret://") for item in child):
                        continue
                if any(token in lowered for token in sensitive) and child not in (None, ""):
                    if isinstance(child, str) and child.startswith("secret://"):
                        continue
                    if isinstance(child, (list, tuple, set)) and all(isinstance(item, str) and item.startswith("secret://") for item in child):
                        continue
                    return True
                if BaseLabAdapter._contains_inline_secret(child, lowered):
                    return True
        elif isinstance(value, (list, tuple, set)):
            return any(BaseLabAdapter._contains_inline_secret(item, key) for item in value)
        elif isinstance(value, str) and (BaseLabAdapter._text_contains_inline_secret(value) or (any(token in key for token in sensitive) and value and not value.startswith("secret://"))):
            return True
        return False

    @staticmethod
    def _text_contains_inline_secret(value: str) -> bool:
        """Detect common key-value secret material embedded in payload text."""
        return re.search(r"(?i)\b(?:password|passwd|secret|token|community|private[-_ ]key)\s*[:=]\s*(?!secret://)\S+", value) is not None

    @staticmethod
    def sanitize_text(value: str) -> str:
        """Redact common secret-bearing text before returning it to callers."""
        sanitized = re.sub(r"(?im)^(\s*(?:password|secret|token|community|private[- ]key)\s*[:=]\s*)\S+", r"\1[REDACTED]", value)
        return re.sub(r"(?i)(secret://)\S+", r"\1[REFERENCE]", sanitized)
