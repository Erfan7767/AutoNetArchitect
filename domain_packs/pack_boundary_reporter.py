from __future__ import annotations

from typing import Any


class PackBoundaryReporter:
    """Report sector boundary, pack conflicts, and unresolved governance findings."""

    def report(self, context: dict[str, Any], guard_result: dict[str, Any]) -> dict[str, Any]:
        policy = guard_result.get("policy", {})
        return {
            "workflow_id": context.get("workflow_id"),
            "selected_pack": context.get("selected_pack"),
            "active_packs": list(context.get("active_packs", [])),
            "activation_status": guard_result.get("status"),
            "production_activation": guard_result.get("production_activation", False),
            "boundary_findings": guard_result.get("reasons", []),
            "pack_conflicts": policy.get("conflicts", []),
            "unknown_packs": policy.get("unknown_packs", []),
            "inheritance_policy": policy.get("inheritance_policy", {}),
            "review_required": context.get("review_required", True),
            "review_completed": context.get("review_completed", False),
            "source_of_truth": context.get("source_of_truth", "requirements_document"),
            "evidence_ids": list(context.get("evidence_ids", [])),
        }
