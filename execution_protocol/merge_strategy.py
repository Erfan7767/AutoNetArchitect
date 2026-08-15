"""Policies for deterministic multi-phase output merging."""
from __future__ import annotations

class MergeStrategy:
    """Resolve package, initializer, and class extension merges."""
    def policy_for(self, conflict_type: str) -> str:
        """Return the policy name for a supported conflict."""
        policies = {'same_package':'merge_non_overlapping_files','same_init':'union_exports_preserving_order','class_extension':'apply_ast_method_merge'}
        if conflict_type not in policies: raise KeyError(conflict_type)
        return policies[conflict_type]
