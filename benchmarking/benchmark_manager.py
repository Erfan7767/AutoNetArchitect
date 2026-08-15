"""Repeatable benchmark run management."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .engineer_baseline import EngineerBaselineRegistry
from .scenario_corpus import ScenarioCorpus


class BenchmarkObservation(BaseModel):
    """One recorded system result for a corpus scenario."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str
    scenario_id: str
    system_output: dict[str, Any] = Field(default_factory=dict)
    engineer_baseline_id: str | None = None
    actual_outcome: str = "not_recorded"
    evidence_ids: tuple[str, ...] = ()
    metric_inputs: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BenchmarkRun(BaseModel):
    """Immutable-style run snapshot with repeatability metadata."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    corpus_fingerprint: str
    scenario_ids: tuple[str, ...]
    observation_ids: tuple[str, ...]
    repeatability_key: str
    started_at: datetime
    finalized_at: datetime | None = None
    status: str = "open"


class BenchmarkManager(BaseDesigner):
    """Manage benchmark data collection while keeping evaluation separate."""

    def __init__(self, *, corpus: ScenarioCorpus | None = None, baselines: EngineerBaselineRegistry | None = None) -> None:
        """Initialize manager with scenario and baseline registries."""
        super().__init__("BenchmarkManager")
        self.corpus = corpus or ScenarioCorpus()
        self.baselines = baselines or EngineerBaselineRegistry()
        self._runs: dict[str, BenchmarkRun] = {}
        self._observations: dict[str, BenchmarkObservation] = {}
        self.record_decision("benchmark_manager_policy", "record_only_repeatable", "manager records observations and fingerprints; metric and maturity decisions remain separate")

    def start_run(self, run_id: str) -> BenchmarkRun:
        """Start a deterministic run snapshot."""
        if run_id in self._runs:
            raise ValueError(f"benchmark run already exists: {run_id}")
        run = BenchmarkRun(run_id=run_id, corpus_fingerprint=self.corpus.fingerprint(), scenario_ids=tuple(item.scenario_id for item in self.corpus.all()), observation_ids=(), repeatability_key=self._repeatability_key(run_id), started_at=datetime.now(timezone.utc))
        self._runs[run_id] = run
        return run

    def record_observation(self, run_id: str, observation: BenchmarkObservation) -> BenchmarkObservation:
        """Record one observation for a known scenario and optional baseline."""
        if run_id not in self._runs:
            raise KeyError(f"benchmark run not found: {run_id}")
        self.corpus.get(observation.scenario_id)
        if observation.engineer_baseline_id is not None and not any(item.baseline_id == observation.engineer_baseline_id for item in self.baselines.all()):
            raise ValueError(f"engineer baseline not found: {observation.engineer_baseline_id}")
        if observation.observation_id in self._observations:
            raise ValueError(f"observation already exists: {observation.observation_id}")
        self._observations[observation.observation_id] = observation
        current = self._runs[run_id]
        self._runs[run_id] = current.model_copy(update={"observation_ids": current.observation_ids + (observation.observation_id,)})
        return observation

    def finalize(self, run_id: str) -> BenchmarkRun:
        """Finalize a run snapshot without interpreting its metrics."""
        current = self._runs[run_id]
        finalized = current.model_copy(update={"finalized_at": datetime.now(timezone.utc), "status": "finalized"})
        self._runs[run_id] = finalized
        return finalized

    def get_run(self, run_id: str) -> BenchmarkRun:
        """Return a run snapshot."""
        return self._runs[run_id]

    def observations(self, run_id: str) -> tuple[BenchmarkObservation, ...]:
        """Return observations belonging to a run."""
        run = self._runs[run_id]
        return tuple(self._observations[item] for item in run.observation_ids)

    def _repeatability_key(self, run_id: str) -> str:
        """Create a deterministic key from run ID and corpus fingerprint."""
        payload = json.dumps({"run_id": run_id, "corpus": self.corpus.fingerprint()}, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
