"""Provider-neutral lab integration and validation workflows."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Protocol, Sequence


class LabState(str, Enum):
    """Lifecycle states for lab operations."""

    PREVIEW_ONLY = "preview_only"
    EXECUTED = "executed"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_UNSUPPORTED = "blocked_unsupported"
    FAILED = "failed"


class GoldenStatus(str, Enum):
    """Comparison states for lab observations and golden outputs."""

    MATCHED = "matched"
    MISMATCH = "mismatch"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"


@dataclass(frozen=True)
class LabTopology:
    """Provider-neutral topology intent for a validation lab."""

    topology_id: str
    nodes: tuple[dict[str, Any], ...]
    links: tuple[dict[str, Any], ...] = ()
    variables: dict[str, Any] = field(default_factory=dict)
    design_ids: tuple[str, ...] = ()
    source_of_truth_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize topology intent."""
        return asdict(self) | {"design_ids": list(self.design_ids), "source_of_truth_ids": list(self.source_of_truth_ids)}


@dataclass(frozen=True)
class LabConfig:
    """Configuration payload derived from a versioned artifact or explicit lab input."""

    device_id: str
    vendor: str
    platform: str
    rendered_config: str
    artifact_id: str = ""
    artifact_hash: str = ""
    decision_ids: tuple[str, ...] = ()
    secret_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize config metadata without resolving secrets."""
        return asdict(self) | {"decision_ids": list(self.decision_ids), "secret_references": list(self.secret_references)}


@dataclass(frozen=True)
class LabOperation:
    """Auditable result for one lab provider operation."""

    provider: str
    operation: str
    state: str
    detail: str
    validation_only: bool = True
    production_change_control_required: bool = True
    payload_hash: str = ""
    evidence_ids: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    provider_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the operation contract."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids), "required_human_inputs": list(self.required_human_inputs)}


@dataclass(frozen=True)
class LabVerificationExecution:
    """Provider verification result containing observations and raw-evidence reference."""

    operation: LabOperation
    observations: dict[str, Any] = field(default_factory=dict)
    raw_outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize verification execution."""
        return asdict(self) | {"operation": self.operation.to_dict()}


@dataclass(frozen=True)
class GoldenComparison:
    """Deterministic comparison between observations and approved golden outputs."""

    status: str
    matched_keys: tuple[str, ...] = ()
    differing_keys: tuple[str, ...] = ()
    missing_keys: tuple[str, ...] = ()
    unexpected_keys: tuple[str, ...] = ()
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize comparison details."""
        return asdict(self) | {
            "matched_keys": list(self.matched_keys),
            "differing_keys": list(self.differing_keys),
            "missing_keys": list(self.missing_keys),
            "unexpected_keys": list(self.unexpected_keys),
        }


@dataclass(frozen=True)
class LabVerificationReport:
    """Complete lab verification result and its non-production boundary."""

    execution: LabVerificationExecution
    comparison: GoldenComparison
    validation_only: bool = True
    production_change_control_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report."""
        return {
            "execution": self.execution.to_dict(),
            "comparison": self.comparison.to_dict(),
            "validation_only": self.validation_only,
            "production_change_control_required": self.production_change_control_required,
        }


class LabAdapter(Protocol):
    """Protocol implemented by each lab provider adapter."""

    provider_name: str

    def deploy_topology(self, topology: LabTopology) -> LabOperation:
        """Deploy a topology to the provider validation environment."""
        raise TypeError("LabAdapter.deploy_topology requires a concrete provider adapter")

    def push_config(self, config: LabConfig) -> LabOperation:
        """Push one configuration into the provider validation environment."""
        raise TypeError("LabAdapter.push_config requires a concrete provider adapter")

    def run_verification(self, plan: Mapping[str, Any]) -> LabVerificationExecution:
        """Run or collect lab verification observations."""
        raise TypeError("LabAdapter.run_verification requires a concrete provider adapter")


class LabManager:
    """Coordinate lab adapters while preserving a strict validation-only boundary."""

    SENSITIVE_KEYS = ("password", "passwd", "secret", "token", "private_key", "api_key", "community")

    def __init__(self, adapters: Iterable[LabAdapter] | None = None) -> None:
        """Create a manager with explicitly registered adapters."""
        self._adapters: dict[str, LabAdapter] = {}
        for adapter in adapters or ():
            self.register_adapter(adapter)

    def register_adapter(self, adapter: LabAdapter) -> None:
        """Register one provider adapter by its stable provider name."""
        if not adapter.provider_name or not adapter.provider_name.strip():
            raise ValueError("lab adapter provider_name is required")
        self._adapters[adapter.provider_name.lower()] = adapter

    def adapter(self, provider: str) -> LabAdapter:
        """Return a registered provider adapter."""
        key = str(provider).strip().lower()
        try:
            return self._adapters[key]
        except KeyError as exc:
            raise KeyError(f"lab provider is not registered: {provider}") from exc

    def deploy_topology(self, provider: str, topology: LabTopology | Mapping[str, Any]) -> LabOperation:
        """Deploy a topology to a lab provider, never to production."""
        normalized = self._normalize_topology(topology)
        if normalized is None:
            return self._blocked(
                provider,
                "deploy_topology",
                "topology intent is missing or incomplete",
                ("topology_id", "nodes"),
                LabState.BLOCKED_MISSING_HUMAN_DATA.value,
            )
        return self.adapter(provider).deploy_topology(normalized)

    def push_configs(self, provider: str, configs: Sequence[LabConfig | Mapping[str, Any] | Any]) -> tuple[LabOperation, ...]:
        """Push versioned configurations to the lab after rejecting inline secrets."""
        if not configs:
            return (
                self._blocked(
                    provider,
                    "push_config",
                    "no configuration artifacts were supplied",
                    ("configs",),
                    LabState.BLOCKED_MISSING_HUMAN_DATA.value,
                ),
            )
        adapter = self.adapter(provider)
        results: list[LabOperation] = []
        for raw in configs:
            config = self._normalize_config(raw)
            if config is None:
                results.append(
                    self._blocked(
                        provider,
                        "push_config",
                        "configuration artifact is incomplete or contains inline secret material",
                        ("device_id", "rendered_config", "secret_manager_reference"),
                        LabState.BLOCKED_MISSING_HUMAN_DATA.value,
                    )
                )
            else:
                results.append(adapter.push_config(config))
        return tuple(results)

    def run_verification(
        self, provider: str, plan: Mapping[str, Any], golden_outputs: Mapping[str, Any] | None = None
    ) -> LabVerificationReport:
        """Run provider verification and compare it to supplied golden outputs."""
        if not plan:
            execution = LabVerificationExecution(
                self._blocked(
                    provider, "run_verification", "verification plan is missing", ("plan",), LabState.BLOCKED_MISSING_HUMAN_DATA.value
                )
            )
        else:
            execution = self.adapter(provider).run_verification(plan)
        comparison = self.compare_golden(execution.observations, golden_outputs)
        return LabVerificationReport(execution, comparison)

    @staticmethod
    def compare_golden(observations: Mapping[str, Any] | None, golden_outputs: Mapping[str, Any] | None) -> GoldenComparison:
        """Compare normalized mappings without treating missing golden data as a match."""
        if observations is None or golden_outputs is None:
            return GoldenComparison(GoldenStatus.NOT_VERIFIABLE.value, detail="observations and approved golden outputs are both required")
        observed = dict(observations)
        golden = dict(golden_outputs)
        observed_keys = set(observed)
        golden_keys = set(golden)
        missing = tuple(sorted(golden_keys - observed_keys))
        unexpected = tuple(sorted(observed_keys - golden_keys))
        matched: list[str] = []
        differing: list[str] = []
        for key in sorted(observed_keys & golden_keys):
            if LabManager._canonical(observed[key]) == LabManager._canonical(golden[key]):
                matched.append(key)
            else:
                differing.append(key)
        status = GoldenStatus.MATCHED.value if not missing and not unexpected and not differing else GoldenStatus.MISMATCH.value
        return GoldenComparison(
            status,
            tuple(matched),
            tuple(differing),
            missing,
            unexpected,
            "golden outputs matched" if status == GoldenStatus.MATCHED.value else "observations differ from golden outputs",
        )

    @staticmethod
    def _canonical(value: Any) -> str:
        """Canonicalize arbitrary JSON-like lab values for deterministic comparison."""
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

    @staticmethod
    def _normalize_topology(value: LabTopology | Mapping[str, Any]) -> LabTopology | None:
        """Normalize a topology without inventing nodes, links, or identifiers."""
        if isinstance(value, LabTopology):
            return value if value.topology_id and value.nodes else None
        if not isinstance(value, Mapping) or not value.get("topology_id") or not value.get("nodes"):
            return None
        nodes = tuple(dict(node) for node in value["nodes"] if isinstance(node, Mapping))
        links = tuple(dict(link) for link in value.get("links", ()) if isinstance(link, Mapping))
        if not nodes:
            return None
        return LabTopology(
            str(value["topology_id"]),
            nodes,
            links,
            dict(value.get("variables", {})),
            tuple(str(item) for item in value.get("design_ids", ())),
            tuple(str(item) for item in value.get("source_of_truth_ids", ())),
        )

    @classmethod
    def _normalize_config(cls, value: LabConfig | Mapping[str, Any] | Any) -> LabConfig | None:
        """Normalize a config artifact and reject likely inline secrets."""
        if isinstance(value, LabConfig):
            return value if value.device_id and value.rendered_config and not cls._contains_inline_secret(value.to_dict()) else None
        if hasattr(value, "to_dict"):
            value = value.to_dict()
        if not isinstance(value, Mapping):
            return None
        rendered = value.get("rendered_config", "")
        if (
            not value.get("device_id")
            or not rendered
            or cls._contains_inline_secret(value)
            or cls._text_contains_inline_secret(str(rendered))
        ):
            return None
        return LabConfig(
            str(value["device_id"]),
            str(value.get("vendor", "")),
            str(value.get("platform", "")),
            str(rendered),
            str(value.get("artifact_id", "")),
            str(value.get("artifact_hash", "")),
            tuple(str(item) for item in value.get("decision_ids", ())),
            tuple(str(item) for item in value.get("secret_references", ())),
        )

    @classmethod
    def _contains_inline_secret(cls, value: Any, key: str = "") -> bool:
        """Detect secret-like keys containing values that are not references."""
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                lowered = str(child_key).lower()
                if "reference" in lowered and isinstance(child, (list, tuple, set)):
                    if all(not isinstance(item, str) or item.startswith("secret://") for item in child):
                        continue
                if any(token in lowered for token in cls.SENSITIVE_KEYS) and child not in (None, ""):
                    if isinstance(child, str) and child.startswith("secret://"):
                        continue
                    if isinstance(child, (list, tuple, set)) and all(
                        isinstance(item, str) and item.startswith("secret://") for item in child
                    ):
                        continue
                    return True
                if cls._contains_inline_secret(child, lowered):
                    return True
        elif isinstance(value, (list, tuple)):
            return any(cls._contains_inline_secret(item, key) for item in value)
        elif isinstance(value, str) and any(token in key for token in cls.SENSITIVE_KEYS) and value and not value.startswith("secret://"):
            return True
        return False

    @staticmethod
    def _text_contains_inline_secret(value: str) -> bool:
        """Detect common key-value secret material embedded in rendered config text."""
        return re.search(r"(?i)\b(?:password|passwd|secret|token|community|private[-_ ]key)\s*[:=]\s*(?!secret://)\S+", value) is not None

    @staticmethod
    def _blocked(provider: str, operation: str, detail: str, required: tuple[str, ...], state: str) -> LabOperation:
        """Create a blocked operation with explicit production boundary metadata."""
        return LabOperation(str(provider), operation, state, detail, True, True, required_human_inputs=required)
