"""Weighted risk analysis for network changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord

from .change_models import ChangeCategory, ChangeRequest, RiskAssessment, RiskLevel


class ChangeRiskAnalyzer:
    """Calculate bounded risk from explicit factors and context."""

    DEFAULT_WEIGHTS = {"scope": 1.4, "complexity": 1.4, "reversibility": 1.3, "testing": 1.2, "experience": 1.0, "timing": 1.0, "dependencies": 1.2}

    def analyze(
        self,
        request: ChangeRequest,
        *,
        lab_tested: bool | None = None,
        during_maintenance_window: bool | None = None,
        experience: str = "first_time",
        dependencies: str = "unknown",
        reversibility: str = "fully_reversible",
        complexity: str | None = None,
        core_infrastructure: bool | None = None,
        sector: str = "general",
        factor_weights: Mapping[str, float] | None = None,
    ) -> RiskAssessment:
        """Return a weighted risk assessment and record assumptions on the request."""
        factors = {
            "scope": self._scope_score(request, core_infrastructure),
            "complexity": self._complexity_score(request, complexity),
            "reversibility": self._reversibility_score(reversibility),
            "testing": self._testing_score(lab_tested),
            "experience": self._experience_score(experience),
            "timing": self._timing_score(during_maintenance_window),
            "dependencies": self._dependency_score(dependencies),
        }
        weights = dict(self.DEFAULT_WEIGHTS)
        if sector.lower() == "banking":
            weights["dependencies"] *= 1.2
            weights["reversibility"] *= 1.15
        weights.update({str(key): float(value) for key, value in (factor_weights or {}).items()})
        weighted_total = sum(factors[key] * weights.get(key, 1.0) for key in factors)
        weight_total = sum(weights.get(key, 1.0) for key in factors)
        score = round(weighted_total / weight_total, 2) if weight_total else 0.0
        level = self._level(score)
        mitigations = self._mitigations(factors, lab_tested, during_maintenance_window, dependencies, reversibility)
        rationale = f"weighted risk score {score:.2f}/10 derived from explicit scope, complexity, reversibility, testing, experience, timing, and dependency factors"
        assessment = RiskAssessment(score, level, factors, weights, tuple(mitigations), rationale, tuple(request.history_ids))
        request.risk_assessment = assessment
        request.decision_records.append(DecisionRecord("ChangeRiskAnalyzer", f"{request.change_id}:risk", level, ["unweighted_average", "weighted_average"], {"unweighted_average": "weighted matrix is the V1 policy", "weighted_average": "selected"}))
        if lab_tested is None:
            request.assumptions.append(Assumption("lab_tested", "unknown", "absence of lab evidence does not become a fabricated test result", True))
        if during_maintenance_window is None:
            request.assumptions.append(Assumption("maintenance_window_context", "unknown", "timing risk cannot be inferred without a window", True))
        if dependencies == "unknown":
            request.assumptions.append(Assumption("dependencies", "unknown", "dependency risk remains elevated until mapped", True))
        request.status = "risk_assessed"
        return assessment

    @staticmethod
    def _scope_score(request: ChangeRequest, core: bool | None) -> int:
        """Map explicit scope to a 1-10 factor."""
        sites = len({site.site_id for site in request.affected_sites})
        devices = len(request.affected_devices)
        if core is True or any(device.core_infrastructure for device in request.affected_devices):
            return 10
        if sites > 1:
            return 7
        if devices > 1:
            return 5
        return 2 if devices == 1 else 4

    @staticmethod
    def _complexity_score(request: ChangeRequest, complexity: str | None) -> int:
        """Map change category and explicit complexity."""
        value = str(complexity or "").lower()
        if request.change_category == ChangeCategory.MIGRATION.value or value == "migration":
            return 10
        if request.change_category == ChangeCategory.TOPOLOGY.value or value == "topology":
            return 8
        if len(request.config_changes) > 3 or value in {"multi_step", "complex"}:
            return 6
        return 2

    @staticmethod
    def _reversibility_score(value: str) -> int:
        """Map rollback reversibility to a risk factor."""
        normalized = str(value).lower()
        return 2 if normalized == "fully_reversible" else 6 if normalized == "partially_reversible" else 10

    @staticmethod
    def _testing_score(value: bool | None) -> int:
        """Give lower risk to explicit lab evidence."""
        return 2 if value is True else 7 if value is False else 8

    @staticmethod
    def _experience_score(value: str) -> int:
        """Map operator or organization experience."""
        return 2 if str(value).lower() in {"standard", "experienced", "repeat"} else 6

    @staticmethod
    def _timing_score(value: bool | None) -> int:
        """Map maintenance-window evidence."""
        return 2 if value is True else 7 if value is False else 8

    @staticmethod
    def _dependency_score(value: str) -> int:
        """Map dependency evidence."""
        normalized = str(value).lower()
        return 2 if normalized in {"none", "no_dependencies"} else 7 if normalized in {"cascading", "high"} else 8

    @staticmethod
    def _level(score: float) -> str:
        """Apply the specified score thresholds."""
        if score <= 3:
            return RiskLevel.LOW.value
        if score <= 6:
            return RiskLevel.MEDIUM.value
        if score <= 8:
            return RiskLevel.HIGH.value
        return RiskLevel.CRITICAL.value

    @staticmethod
    def _mitigations(factors: Mapping[str, int], lab_tested: bool | None, in_window: bool | None, dependencies: str, reversibility: str) -> list[str]:
        """Generate targeted mitigation actions for elevated factors."""
        mitigations: list[str] = []
        if factors["scope"] >= 7:
            mitigations.append("split scope by device or site and add staged checkpoints")
        if factors["complexity"] >= 7:
            mitigations.append("perform a lab validation and require human checkpoint after each dependency boundary")
        if factors["reversibility"] >= 6:
            mitigations.append("verify a recent tested backup and document the point of no return")
        if lab_tested is not True:
            mitigations.append("obtain lab validation evidence before scheduling a normal change")
        if in_window is not True:
            mitigations.append("schedule inside an approved maintenance window")
        if dependencies not in {"none", "no_dependencies"}:
            mitigations.append("map dependent devices and services before implementation")
        if not mitigations:
            mitigations.append("retain standard prechecks, postchecks, and audit evidence")
        return mitigations
