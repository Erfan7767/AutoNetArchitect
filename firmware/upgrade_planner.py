"""Staged firmware upgrade planning with redundancy-aware sequencing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from .firmware_manager import FirmwareManager, FirmwareUpgradeRequest, UpgradePath


@dataclass(frozen=True)
class UpgradeStage:
    """One ordered stage of a firmware rollout."""

    stage_number: int
    request_ids: tuple[str, ...]
    target_ids: tuple[str, ...]
    redundancy_groups: tuple[str, ...] = ()
    canary: bool = False
    state: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the stage."""
        return asdict(self) | {"request_ids": list(self.request_ids), "target_ids": list(self.target_ids), "redundancy_groups": list(self.redundancy_groups)}


@dataclass(frozen=True)
class UpgradePlan:
    """Complete staged rollout plan and its blocking conditions."""

    plan_id: str
    request_ids: tuple[str, ...]
    stages: tuple[UpgradeStage, ...]
    allowed: bool
    production_ready: bool
    path_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the plan without artifact contents or credentials."""
        return asdict(self) | {"request_ids": list(self.request_ids), "stages": [stage.to_dict() for stage in self.stages], "path_ids": list(self.path_ids), "reasons": list(self.reasons), "required_human_inputs": list(self.required_human_inputs), "evidence_ids": list(self.evidence_ids)}


class UpgradePlanner:
    """Create explicit staged plans from exact registered upgrade paths."""

    def __init__(self, firmware_manager: FirmwareManager) -> None:
        """Create a planner attached to a firmware registry."""
        self.firmware_manager = firmware_manager

    def plan(self, requests: Sequence[FirmwareUpgradeRequest], *, plan_id: str = "", canary_request_ids: Iterable[str] = ()) -> UpgradePlan:
        """Build a stage plan without invoking any driver or implying execution approval."""
        if not requests:
            return UpgradePlan(plan_id or "firmware-plan-empty", (), (), False, False, reasons=("at least one firmware upgrade request is required",), required_human_inputs=("firmware_upgrade_requests",))
        request_ids = tuple(request.request_id for request in requests)
        reasons: list[str] = []
        required_inputs: list[str] = []
        paths: dict[str, UpgradePath] = {}
        seen_request_ids: set[str] = set()
        for request in requests:
            if not request.request_id:
                reasons.append("firmware request ID is mandatory")
            if request.request_id in seen_request_ids:
                reasons.append(f"duplicate firmware request ID: {request.request_id}")
            seen_request_ids.add(request.request_id)
            path = self.firmware_manager.resolve_path(request)
            if path is None:
                reasons.append(f"no exact registered upgrade path for request {request.request_id}")
                required_inputs.append(f"exact_upgrade_path:{request.request_id}")
                continue
            paths[request.request_id] = path
            if path.support_state not in self.firmware_manager.safety_checks.SUPPORTED_PATH_STATES:
                reasons.append(f"upgrade path {path.path_id} is not explicitly supported")
            if not path.evidence_ids:
                reasons.append(f"upgrade path {path.path_id} has no evidence IDs")
                required_inputs.append(f"upgrade_path_evidence:{path.path_id}")
            if not request.dry_run:
                if request.maintenance_window is None:
                    required_inputs.append(f"maintenance_window:{request.request_id}")
                if not request.approved:
                    required_inputs.append(f"approval:{request.request_id}")
                if request.rollback_required and not (request.rollback_image_id or path.rollback_image_id):
                    required_inputs.append(f"rollback_image:{request.request_id}")
        stages = self._stage_requests(requests)
        canaries = set(str(item) for item in canary_request_ids)
        if canaries and not canaries.issubset(set(request_ids)):
            reasons.append("canary request IDs must belong to the plan")
            required_inputs.append("valid_canary_request_ids")
        stages = tuple(UpgradeStage(stage.stage_number, stage.request_ids, stage.target_ids, stage.redundancy_groups, bool(canaries.intersection(stage.request_ids)) or stage.stage_number == 1, stage.state) for stage in stages)
        production_ready = not reasons and not required_inputs and all(not request.dry_run for request in requests)
        allowed = not reasons and not required_inputs
        evidence: set[str] = set()
        for request in requests:
            evidence.update(request.evidence_ids)
            evidence.update(request.image.evidence_ids)
            if request.request_id in paths:
                evidence.update(paths[request.request_id].evidence_ids)
        return UpgradePlan(plan_id or f"firmware-plan-{requests[0].request_id}", request_ids, stages, allowed, production_ready, tuple(path.path_id for path in paths.values()), tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(required_inputs)), tuple(sorted(evidence)))

    def validate_stage(self, plan: UpgradePlan, stage_number: int, completed_request_ids: Iterable[str] = ()) -> tuple[bool, tuple[str, ...]]:
        """Validate that earlier stages are complete and the selected stage is redundancy-safe."""
        completed = {str(item) for item in completed_request_ids}
        stage = next((item for item in plan.stages if item.stage_number == stage_number), None)
        if stage is None:
            return False, (f"stage {stage_number} does not exist",)
        reasons: list[str] = []
        earlier = [item for item in plan.stages if item.stage_number < stage_number]
        for prior in earlier:
            missing = set(prior.request_ids) - completed
            if missing:
                reasons.append(f"prior stage {prior.stage_number} is incomplete: {','.join(sorted(missing))}")
        groups = [group for group in stage.redundancy_groups if group]
        if len(groups) != len(set(groups)):
            reasons.append("stage contains more than one member of a redundancy group")
        return not reasons, tuple(reasons)

    @staticmethod
    def _stage_requests(requests: Sequence[FirmwareUpgradeRequest]) -> tuple[UpgradeStage, ...]:
        """Greedily distribute requests so each stage has at most one member per group."""
        stage_rows: list[list[FirmwareUpgradeRequest]] = []
        for request in requests:
            group = request.target.redundancy_group
            selected: list[FirmwareUpgradeRequest] | None = None
            for row in stage_rows:
                existing_groups = {item.target.redundancy_group for item in row if item.target.redundancy_group}
                if not group or group not in existing_groups:
                    selected = row
                    break
            if selected is None:
                selected = []
                stage_rows.append(selected)
            selected.append(request)
        stages: list[UpgradeStage] = []
        for number, row in enumerate(stage_rows, start=1):
            stages.append(UpgradeStage(number, tuple(item.request_id for item in row), tuple(item.target.target_id for item in row), tuple(dict.fromkeys(item.target.redundancy_group for item in row if item.target.redundancy_group))))
        return tuple(stages)
