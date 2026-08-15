"""Static and sample-render validation for the complete template library."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .models import TemplateValidationReport, TemplateValidationState
from .template_registry import TemplateRegistry
from .template_renderer import TemplateRenderer


class TemplateValidator:
    """Validate templates without declaring unvalidated vendor syntax production-safe."""

    SECRET_PATTERN = re.compile(r"(?i)(?:password|passwd|secret|token|psk|private[_-]?key|api[_-]?key|community)\s*[:=]\s*(['\"])(?!secret://).*?\1")
    IP_PATTERN = re.compile(r"(?<![\w./])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?(?![\w.])")
    UNSAFE_PATTERN = re.compile(r"(?i)\b(?:TODO|placeholder|pass)\b")

    def __init__(self, registry: TemplateRegistry, renderer: TemplateRenderer | None = None) -> None:
        self.registry = registry
        self.renderer = renderer or TemplateRenderer(registry)

    def _source(self, template_id: str) -> str:
        metadata = self.registry.get(template_id)
        if metadata is None:
            raise KeyError(f"unknown template: {template_id}")
        path = Path(self.renderer.template_root) / self.renderer._template_name(metadata.file_path)
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _sample_value(type_name: str) -> Any:
        value = type_name.lower()
        if "bool" in value:
            return False
        if "int" in value or "asn" in value or "vlan" in value:
            return 1
        if "list" in value:
            return []
        if "object" in value:
            return {}
        if "ipv6" in value:
            return "2001:db8::1"
        if "ipv4" in value or "ip" in value:
            return "192.0.2.1"
        return "sample-value"

    def _sample_variables(self, template_id: str) -> dict[str, Any]:
        metadata = self.registry.get(template_id)
        if metadata is None:
            raise KeyError(f"unknown template: {template_id}")
        values = {variable.name: self._sample_value(variable.type_name) for variable in metadata.required_variables}
        values["commands"] = []
        return values

    def validate(self, template_id: str, sample_variables: dict[str, Any] | None = None) -> TemplateValidationReport:
        """Return a detailed report for one template."""
        metadata = self.registry.get(template_id)
        if metadata is None:
            raise KeyError(f"unknown template: {template_id}")
        source = self._source(template_id)
        referenced: set[str] = set()
        syntax_valid = True
        messages: list[str] = []
        try:
            environment = self.renderer._environment()
            from jinja2 import meta
            ast = environment.parse(source)
            referenced = set(meta.find_undeclared_variables(ast))
        except Exception as exc:
            syntax_valid = False
            messages.append(f"jinja_syntax_error:{exc}")
        declared = {variable.name for variable in metadata.required_variables + metadata.optional_variables} | {"commands", "range", "loop", "cycler", "joiner", "namespace"}
        undeclared = tuple(sorted(referenced - declared))
        secret_hits = tuple(match.group(0) for match in self.SECRET_PATTERN.finditer(source))
        ip_hits = tuple(dict.fromkeys(match.group(0) for match in self.IP_PATTERN.finditer(source) if not match.group(0).startswith("192.0.2.")))
        unsafe_hits = tuple(dict.fromkeys(match.group(0) for match in self.UNSAFE_PATTERN.finditer(source)))
        missing_defaults: list[str] = []
        if metadata.required_variables and "else" not in source and "default(" not in source and "commands" not in source:
            missing_defaults.append("safety_critical_condition_without_else_or_default")
        sample_error: str | None = None
        try:
            self.renderer.render(template_id, sample_variables or self._sample_variables(template_id), production=False)
        except Exception as exc:
            sample_error = str(exc)
        if undeclared:
            messages.append("undeclared_variables_not_in_registry")
        if secret_hits:
            messages.append("hardcoded_secret_detected")
        if ip_hits:
            messages.append("hardcoded_ip_literal_detected")
        if unsafe_hits:
            messages.append("unsafe_token_detected")
        if missing_defaults:
            messages.extend(missing_defaults)
        if sample_error:
            messages.append("sample_render_failed")
        if not syntax_valid or undeclared or secret_hits or ip_hits or unsafe_hits or missing_defaults or sample_error:
            state = TemplateValidationState.BLOCKED
        elif metadata.validation_state is TemplateValidationState.VERIFIED:
            state = TemplateValidationState.VERIFIED
        else:
            state = TemplateValidationState.PREVIEW_ONLY
            messages.append("model_version_authoritative_validation_still_required")
        return TemplateValidationReport(template_id, syntax_valid, tuple(sorted(referenced)), undeclared, secret_hits, ip_hits, unsafe_hits, tuple(missing_defaults), sample_error, state, tuple(messages))

    def validate_all(self) -> list[TemplateValidationReport]:
        """Validate all registered templates in deterministic order."""
        return [self.validate(record.template_id) for record in self.registry.all()]
