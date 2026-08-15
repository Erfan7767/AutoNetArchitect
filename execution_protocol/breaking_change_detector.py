"""Aggregate graph and signature findings into remediation advice."""
from __future__ import annotations
from typing import Any

class BreakingChangeDetector:
    """Classify compatibility findings and suggest fixes."""
    def detect(self, graph_report: dict[str, Any], signature_changes: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
        """Return breaking, additive, and deprecated change groups."""
        breaking = [{'kind': 'cycle', 'detail': str(c), 'fix_strategy': 'remove_dependency_edge'} for c in graph_report.get('cycles', [])]
        breaking += [{**item, 'fix_strategy': 'restore_compatible_signature'} for item in signature_changes]
        return {'breaking_changes': breaking, 'non_breaking_additions': [], 'deprecated_items': []}
