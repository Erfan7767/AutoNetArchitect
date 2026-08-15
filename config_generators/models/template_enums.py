"""Enumerations used by the complete template library."""
from __future__ import annotations

from enum import Enum


class TemplateValidationState(str, Enum):
    """Lifecycle state of template validation."""

    VERIFIED = "verified"
    PREVIEW_ONLY = "preview_only"
    BLOCKED = "blocked"
    REQUIRES_AUTHORITATIVE_MODEL_VALIDATION = "requires_authoritative_model_validation"


class TemplateVariableSource(str, Enum):
    """Allowed sources for template variables."""

    DESIGN_ARTIFACT = "design_artifact"
    EQUIPMENT_DATA = "equipment_data"
    SECRET_REFERENCE = "secret_reference"
    HUMAN_SUPPLIED = "human_supplied"
    PROJECT_CONFIGURATION = "project_configuration"
    ASSUMPTION = "assumption"
    DEFAULT = "default"
