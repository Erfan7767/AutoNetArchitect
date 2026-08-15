"""Enums for offline configuration validation states."""
from __future__ import annotations

from enum import Enum


class ValidationStatus(str, Enum):
    """Overall validation outcome."""

    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED = "FAILED"


class CoverageStatus(str, Enum):
    """Evidence coverage level for a command or section."""

    VALIDATED = "validated"
    PARTIALLY_VALIDATED = "partially_validated"
    NOT_COVERED = "not_covered"


class Severity(str, Enum):
    """Diagnostic severity."""

    ERROR = "error"
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ValidationStage(str, Enum):
    """Validation pipeline stages."""

    STRUCTURAL = "structural"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    CROSS_REFERENCE = "cross_reference"
    SECRET_SCAN = "secret_scan"
    DEPRECATED = "deprecated"
    COMPLETENESS = "completeness"
    IDEMPOTENCY = "idempotency"
