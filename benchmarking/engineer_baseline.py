"""Human engineer baseline contracts for benchmark comparison."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EngineerBaseline(BaseModel):
    """Expected or observed human reference for one scenario."""

    model_config = ConfigDict(extra="forbid")

    baseline_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    engineer_reference: str = Field(min_length=1)
    design_choices: dict[str, Any] = Field(default_factory=dict)
    assumption_quality_score: float = 0.0
    unresolved_handling_score: float = 0.0
    safety_decision: str = "unknown"
    config_correctness_score: float | None = None
    evidence_ids: tuple[str, ...] = ()
    review_status: str = "unreviewed"
    limitations: tuple[str, ...] = ()

    def model_post_init(self, __context: object) -> None:
        """Validate bounded scores."""
        scores = (self.assumption_quality_score, self.unresolved_handling_score)
        if self.config_correctness_score is not None:
            scores += (self.config_correctness_score,)
        if any(not 0.0 <= value <= 1.0 for value in scores):
            raise ValueError("engineer baseline scores must be between zero and one")


class EngineerBaselineRegistry:
    """Registry for human reference baselines."""

    def __init__(self, baselines: tuple[EngineerBaseline, ...] = ()) -> None:
        """Initialize baseline registry."""
        self._baselines: dict[str, EngineerBaseline] = {}
        for baseline in baselines:
            self.register(baseline)

    def register(self, baseline: EngineerBaseline) -> EngineerBaseline:
        """Register one baseline without silently replacing an existing reference."""
        if baseline.baseline_id in self._baselines:
            raise ValueError(f"baseline already exists: {baseline.baseline_id}")
        self._baselines[baseline.baseline_id] = baseline
        return baseline

    def for_scenario(self, scenario_id: str) -> tuple[EngineerBaseline, ...]:
        """Return baselines for one scenario."""
        return tuple(item for item in self._baselines.values() if item.scenario_id == scenario_id)

    def all(self) -> tuple[EngineerBaseline, ...]:
        """Return all baselines."""
        return tuple(self._baselines.values())
