"""Shared vendor validator contract."""
from __future__ import annotations

from typing import Any

from config_validators.models import CoverageStatus, ValidationBlockResult, ValidationLineResult
from config_validators.semantic_validator import SemanticValidator
from config_validators.structural_validator import StructuralValidator
from config_validators.syntax_rule_engine import SyntaxRuleEngine


class BaseVendorValidator:
    """Provide line and block validation for one vendor/platform."""

    vendor = ""
    platform = ""
    platform_key = ""
    command_patterns: dict[str, str] = {}
    hierarchy_rules: dict[str, tuple[str, ...]] = {}
    mode_transitions: dict[str, str] = {}

    def __init__(self, grammar_root: str | None = None) -> None:
        self.engine = SyntaxRuleEngine(grammar_root)
        self.structural = StructuralValidator()
        self.semantic = SemanticValidator()

    def validate_line(self, line: str, context: dict[str, Any] | None = None) -> ValidationLineResult:
        context = context or {}
        return self.engine.validate_line(line, int(context.get("line_number", 1)), self.vendor, self.platform, str(context.get("mode", "global")))

    def validate_block(self, block: str, parent_context: dict[str, Any] | None = None) -> ValidationBlockResult:
        return self.structural.validate(block, self.vendor, self.platform)

    def validate(self, config_text: str) -> list[ValidationLineResult]:
        results = self.engine.validate(config_text, self.vendor, self.platform)
        structural = self.structural.validate(config_text, self.vendor, self.platform)
        semantic = self.semantic.validate(config_text, self.vendor, self.platform)
        diagnostics_by_line: dict[int, list] = {}
        for diagnostic in structural.diagnostics + tuple(semantic):
            if diagnostic.line_number is not None:
                diagnostics_by_line.setdefault(diagnostic.line_number, []).append(diagnostic)
        updated = []
        for result in results:
            extra = tuple(diagnostics_by_line.get(result.line_number, []))
            if extra:
                updated.append(ValidationLineResult(result.line_number, result.line, False, CoverageStatus.VALIDATED, result.diagnostics + extra, result.mode_after))
            else:
                updated.append(result)
        return updated
