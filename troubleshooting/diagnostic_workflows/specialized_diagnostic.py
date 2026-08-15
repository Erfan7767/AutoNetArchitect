"""Shared implementation for the Troubleshooting Engine diagnostic workflows."""

from __future__ import annotations

from typing import Iterable

from .base_diagnostic import BaseDiagnostic, DiagnosticDecisionTree, DiagnosticWorkflowOutput
from ..models import EvidenceCollection, Hypothesis


class SpecializedDiagnostic(BaseDiagnostic):
    """Reusable workflow implementation parameterized by layer-specific checks."""

    diagnostic_id = "specialized_diagnostic"
    symptom_class = "unknown"
    required_evidence_types: tuple[str, ...] = ()
    command_catalog: tuple[str, ...] = ()
    findings_terms: tuple[tuple[str, str], ...] = ()
    decision_tree = DiagnosticDecisionTree(tree_id="specialized", direction="divide_and_conquer", nodes=[])

    def execute(self, evidence: EvidenceCollection, hypotheses: Iterable[Hypothesis] = ()) -> DiagnosticWorkflowOutput:
        """Execute a bounded workflow using supplied evidence only."""
        findings: list[str] = []
        text = " ".join(f"{item.raw_data} {item.parsed_data}" for item in evidence.items).lower()
        for term, finding in self.findings_terms:
            if term.lower() in text:
                findings.append(finding)
        if not findings:
            findings.append(f"no explicit {self.symptom_class} fault indicator was confirmed by supplied evidence")
        for required in self.required_evidence_types:
            if not any(required in item.request_type or required in item.source.value for item in evidence.items):
                self.assumptions.append(self._assumption(required))
        return self._build_output(evidence, hypotheses, findings)

    def get_required_commands(self, vendor: str, platform: str) -> list[str]:
        """Return only catalogued read-only commands."""
        del vendor, platform
        return list(self.command_catalog)

    @staticmethod
    def _assumption(key: str):
        """Create an explicit missing-evidence assumption."""
        from designers.base_designer import Assumption

        return Assumption(f"required_evidence:{key}", "not_supplied", "workflow cannot assert this layer without explicit evidence", True)
