"""Typed models for registry records, variables, audits, and composition results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .template_enums import TemplateValidationState, TemplateVariableSource


@dataclass(frozen=True)
class TemplateVariable:
    """Variable contract declared by a template."""

    name: str
    type_name: str
    description: str
    required: bool = False
    default: Any = None
    sources: tuple[TemplateVariableSource, ...] = ()


@dataclass(frozen=True)
class TemplateMetadata:
    """Central registry metadata for one template."""

    template_id: str
    vendor: str
    platform: str
    feature_area: str
    file_path: str
    required_variables: tuple[TemplateVariable, ...] = ()
    optional_variables: tuple[TemplateVariable, ...] = ()
    min_platform_version: str | None = None
    max_platform_version: str | None = None
    depends_on_templates: tuple[str, ...] = ()
    feature_guard_required: str = ""
    evidence_reference: str = ""
    last_validated_version: str = ""
    validation_state: TemplateValidationState = TemplateValidationState.REQUIRES_AUTHORITATIVE_MODEL_VALIDATION
    description: str = ""


@dataclass(frozen=True)
class TemplateAuditEvent:
    """Traceable rendering event."""

    event_id: str
    template_id: str
    status: str
    variable_names: tuple[str, ...]
    decision_ids: tuple[str, ...]
    evidence_reference: str
    secret_references: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class VariableResolution:
    """Resolved, defaulted, assumed, and unresolved template variables."""

    values: dict[str, Any] = field(default_factory=dict)
    unresolved: tuple[str, ...] = ()
    defaulted: tuple[str, ...] = ()
    assumed: tuple[str, ...] = ()
    secret_references: tuple[str, ...] = ()
    source_by_variable: dict[str, TemplateVariableSource] = field(default_factory=dict)


@dataclass(frozen=True)
class TemplateValidationReport:
    """Validation report for one or more templates."""

    template_id: str
    valid_syntax: bool
    referenced_variables: tuple[str, ...] = ()
    undeclared_variables: tuple[str, ...] = ()
    hardcoded_secret_paths: tuple[str, ...] = ()
    hardcoded_ip_literals: tuple[str, ...] = ()
    unsafe_output_tokens: tuple[str, ...] = ()
    missing_safety_defaults: tuple[str, ...] = ()
    sample_render_error: str | None = None
    status: TemplateValidationState = TemplateValidationState.BLOCKED
    messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompositionResult:
    """Output of composing a device configuration from template fragments."""

    device_id: str
    platform: str
    status: str
    rendered_config: str
    template_ids: tuple[str, ...]
    decision_ids: tuple[str, ...]
    evidence_references: tuple[str, ...]
    unsupported_templates: tuple[str, ...] = ()
    audit_events: tuple[TemplateAuditEvent, ...] = ()
