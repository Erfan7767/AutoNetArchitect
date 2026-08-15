"""Repeatable benchmark scenario corpus contracts."""
from __future__ import annotations

from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class ScenarioClass(str, Enum):
    """Benchmark scenario dimensions."""

    GREENFIELD = "greenfield"
    BROWNFIELD = "brownfield"
    MULTI_SITE = "multi_site"
    VENDOR_SPECIFIC = "vendor_specific"
    AMBIGUOUS_INPUTS = "ambiguous_inputs"
    INCOMPLETE_DATA = "incomplete_data"
    HIGH_RISK_DEPLOYMENT = "high_risk_deployment"


class BenchmarkScenario(BaseModel):
    """One deterministic benchmark case with expected safe behavior."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    classes: tuple[ScenarioClass, ...]
    vendor: str | None = None
    input_artifact: dict[str, Any] = Field(default_factory=dict)
    expected_decision_type: str = "design"
    expected_safety_decision: str = Field(min_length=1)
    expected_abstention: bool = False
    required_evidence: tuple[str, ...] = ()
    known_constraints: tuple[str, ...] = ()
    risk_level: str = "medium"
    corpus_version: str = "1.0"


class ScenarioCorpus(BaseDesigner):
    """Load, validate, and fingerprint a stable benchmark corpus."""

    def __init__(self, scenarios: Iterable[BenchmarkScenario] | None = None) -> None:
        """Initialize corpus from explicit scenarios or built-in deterministic cases."""
        super().__init__("ScenarioCorpus")
        self._scenarios: dict[str, BenchmarkScenario] = {}
        for scenario in scenarios or self.default_scenarios():
            self.register(scenario)
        self.record_decision("corpus_repeatability", self.fingerprint(), "scenario corpus uses deterministic identifiers and serialized inputs")

    @staticmethod
    def default_scenarios() -> tuple[BenchmarkScenario, ...]:
        """Return the minimum scenario coverage requested by the benchmark layer."""
        return (
            BenchmarkScenario(scenario_id="greenfield-campus", title="Greenfield enterprise campus", classes=(ScenarioClass.GREENFIELD,), vendor="cisco", input_artifact={"sites": 1, "design_state": "new"}, expected_safety_decision="decide_with_review", required_evidence=("requirements", "site_data"), risk_level="medium"),
            BenchmarkScenario(scenario_id="brownfield-branch", title="Brownfield branch with unknown drift", classes=(ScenarioClass.BROWNFIELD, ScenarioClass.INCOMPLETE_DATA), vendor="fortinet", input_artifact={"sites": 1, "discovered_state": "partial"}, expected_safety_decision="abstain_pending_data", expected_abstention=True, required_evidence=("discovery", "current_config"), known_constraints=("unknown_current_acl",), risk_level="high"),
            BenchmarkScenario(scenario_id="multi-site-wan", title="Multi-site WAN with branch variation", classes=(ScenarioClass.MULTI_SITE,), vendor="juniper", input_artifact={"sites": "human_supplied", "wan": "multi_provider"}, expected_safety_decision="decide_with_review", required_evidence=("site_inventory", "provider_handoffs"), risk_level="high"),
            BenchmarkScenario(scenario_id="vendor-feature-gap", title="Vendor-specific unsupported feature", classes=(ScenarioClass.VENDOR_SPECIFIC, ScenarioClass.AMBIGUOUS_INPUTS), vendor="mikrotik", input_artifact={"feature": "unverified_platform_capability"}, expected_safety_decision="block_unsupported_claim", expected_abstention=True, required_evidence=("capability_evidence",), known_constraints=("exact_version_missing",), risk_level="high"),
            BenchmarkScenario(scenario_id="ambiguous-security-intent", title="Ambiguous security intent", classes=(ScenarioClass.AMBIGUOUS_INPUTS,), input_artifact={"intent": "ambiguous"}, expected_safety_decision="request_clarification", expected_abstention=True, required_evidence=("security_intent",), risk_level="high"),
            BenchmarkScenario(scenario_id="incomplete-wireless", title="Wireless plan without RF survey", classes=(ScenarioClass.INCOMPLETE_DATA,), vendor="aruba", input_artifact={"floor_dimensions": None, "survey": None}, expected_safety_decision="preview_only_pending_survey", expected_abstention=True, required_evidence=("floor_dimensions", "rf_survey"), risk_level="high"),
            BenchmarkScenario(scenario_id="high-risk-production-change", title="High-risk production deployment", classes=(ScenarioClass.HIGH_RISK_DEPLOYMENT,), vendor="paloalto", input_artifact={"production": True, "rollback": "required"}, expected_safety_decision="requires_approval_and_backup", required_evidence=("backup", "rollback_plan", "verification"), risk_level="critical"),
        )

    def register(self, scenario: BenchmarkScenario) -> BenchmarkScenario:
        """Register a scenario and reject duplicate identifiers."""
        if scenario.scenario_id in self._scenarios:
            raise ValueError(f"scenario already exists: {scenario.scenario_id}")
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    def get(self, scenario_id: str) -> BenchmarkScenario:
        """Return a scenario by ID."""
        return self._scenarios[scenario_id]

    def all(self) -> tuple[BenchmarkScenario, ...]:
        """Return scenarios in stable identifier order."""
        return tuple(self._scenarios[key] for key in sorted(self._scenarios))

    def fingerprint(self) -> str:
        """Return a deterministic corpus fingerprint."""
        payload = [item.model_dump(mode="json") for item in self.all()]
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

    @classmethod
    def from_json(cls, path: str | Path) -> "ScenarioCorpus":
        """Load scenarios from a JSON array without randomization."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("benchmark scenario file must contain a JSON array")
        return cls(BenchmarkScenario.model_validate(item) for item in payload)
