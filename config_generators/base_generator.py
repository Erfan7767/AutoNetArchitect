"""Common contracts for traceable, capability-gated configuration artifacts."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from designers.base_designer import BaseDesigner

from .feature_guards import FeatureGuards


@dataclass(frozen=True)
class DeviceConfig:
    """Versioned configuration artifact with evidence and decision lineage."""

    schema_version: str
    artifact_id: str
    device_id: str
    vendor: str
    platform: str
    os_version: str | None
    status: str
    rendered_config: str
    commands: tuple[str, ...] = ()
    unsupported_log: tuple[dict[str, Any], ...] = ()
    capability_evidence_ids: tuple[str, ...] = ()
    license_evidence_ids: tuple[str, ...] = ()
    command_source_ids: tuple[str, ...] = ()
    decision_ids: tuple[str, ...] = ()
    secret_references: tuple[str, ...] = ()
    created_at: str = ""
    artifact_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the artifact without resolving or exposing secrets."""
        return asdict(self)


@dataclass(frozen=True)
class GenerationResult:
    """Generation response carrying a DeviceConfig and audit records."""

    artifact: DeviceConfig
    decision_records: tuple[Any, ...] = ()
    assumptions: tuple[Any, ...] = ()


class BaseGenerator(BaseDesigner):
    """Render only exact commands that satisfy capability, license, source, and decision gates."""

    SCHEMA_VERSION = "1.0"
    TEMPLATE_NAME = "base.j2"

    def __init__(self, vendor: str, platform: str, template_name: str | None = None, name: str | None = None) -> None:
        super().__init__(name or self.__class__.__name__)
        self.vendor = vendor
        self.platform = platform
        self.template_name = template_name or self.TEMPLATE_NAME
        self.guards = FeatureGuards()
        self.template_root = Path(__file__).parent / "templates"

    @staticmethod
    def _ids(value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,) if value else ()
        if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, dict)):
            return tuple(str(item) for item in value if str(item))
        return ()

    @classmethod
    def _secret_issues(cls, value: Any, path: str = "requirements") -> tuple[tuple[str, str], ...]:
        """Find inline secret material; only secret-manager references are accepted."""
        sensitive_tokens = ("password", "passwd", "secret", "token", "psk", "private_key", "api_key", "community")
        issues: list[tuple[str, str]] = []
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                key_lower = str(key).lower()
                if any(token in key_lower for token in sensitive_tokens):
                    if isinstance(child, str) and child and not child.startswith("secret://"):
                        issues.append((child_path, "inline_secret_value"))
                    elif isinstance(child, list):
                        for index, item in enumerate(child):
                            if isinstance(item, str) and item and not item.startswith("secret://"):
                                issues.append((f"{child_path}[{index}]", "inline_secret_value"))
                issues.extend(cls._secret_issues(child, child_path))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                issues.extend(cls._secret_issues(child, f"{path}[{index}]"))
        return tuple(issues)

    @classmethod
    def _secret_references(cls, requirements: dict[str, Any]) -> tuple[str, ...]:
        references: list[str] = []
        candidate = requirements.get("secret_references", requirements.get("secrets", []))
        if isinstance(candidate, dict):
            candidate = list(candidate.values())
        if isinstance(candidate, list):
            references = [str(value) for value in candidate if isinstance(value, str) and value.startswith("secret://")]
        elif isinstance(candidate, str) and candidate.startswith("secret://"):
            references = [candidate]
        return tuple(dict.fromkeys(references))

    def _render(self, context: dict[str, Any]) -> str:
        """Render a platform template using Jinja2 strict undefined semantics."""
        try:
            from jinja2 import Environment, FileSystemLoader, StrictUndefined
        except ImportError as exc:
            raise RuntimeError("Jinja2 is required for configuration generation") from exc
        environment = Environment(loader=FileSystemLoader(str(self.template_root)), undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)
        template = environment.get_template(self.template_name)
        return template.render(**context)

    def _artifact(self, device_id: str, os_version: str | None, status: str, rendered: str, commands: list[str], unsupported: list[dict[str, Any]], capability_ids: Iterable[str], license_ids: Iterable[str], command_sources: Iterable[str], decision_ids: Iterable[str], secret_references: Iterable[str]) -> DeviceConfig:
        created_at = datetime.now(timezone.utc).isoformat()
        capability_tuple = tuple(dict.fromkeys(str(value) for value in capability_ids))
        license_tuple = tuple(dict.fromkeys(str(value) for value in license_ids))
        source_tuple = tuple(dict.fromkeys(str(value) for value in command_sources))
        decision_tuple = tuple(dict.fromkeys(str(value) for value in decision_ids))
        secret_tuple = tuple(dict.fromkeys(str(value) for value in secret_references))
        unsigned = {"schema_version": self.SCHEMA_VERSION, "device_id": device_id, "vendor": self.vendor, "platform": self.platform, "os_version": os_version, "status": status, "rendered_config": rendered, "commands": commands, "unsupported_log": unsupported, "capability_evidence_ids": capability_tuple, "license_evidence_ids": license_tuple, "command_source_ids": source_tuple, "decision_ids": decision_tuple, "secret_references": secret_tuple}
        artifact_hash = hashlib.sha256(json.dumps(unsigned, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        artifact_id = f"device-config:{self.vendor.lower()}:{self.platform.lower()}:{artifact_hash[:16]}"
        return DeviceConfig(self.SCHEMA_VERSION, artifact_id, device_id, self.vendor, self.platform, os_version, status, rendered, tuple(commands), tuple(unsupported), capability_tuple, license_tuple, source_tuple, decision_tuple, secret_tuple, created_at, artifact_hash)

    def generate(self, requirements: dict[str, Any], production: bool = True) -> GenerationResult:
        """Generate a versioned artifact and never substitute unsupported commands."""
        device = requirements.get("device", requirements)
        if not isinstance(device, dict):
            device = {}
        device_id = str(device.get("device_id", device.get("hostname", "unidentified-device")))
        platform = str(device.get("platform", self.platform))
        os_version = device.get("os_version", device.get("version"))
        if platform.lower() != self.platform.lower():
            self.record_assumption("generator_platform_scope", platform, "The requested platform differs from this generator and requires explicit routing to the correct generator.")
        capability_evidence = requirements.get("capability_evidence", {})
        license_evidence = requirements.get("license_evidence", {})
        default_decisions = self._ids(requirements.get("decision_ids"))
        all_commands: list[str] = []
        unsupported: list[dict[str, Any]] = []
        capability_ids: list[str] = []
        license_ids: list[str] = []
        command_sources: list[str] = []
        decision_ids: list[str] = list(default_decisions)
        secret_references = self._secret_references(requirements)
        secret_issues = self._secret_issues(requirements)
        if secret_issues:
            self.record_assumption("secret_handling", "inline_secret_rejected", "Secrets must remain SecretManager references and cannot be emitted or retained in a configuration artifact.")
            unsupported.append({"feature": "secret_handling", "workflow": self.platform, "reasons": [f"{path}:{reason}" for path, reason in secret_issues], "required_action": "replace inline values with secret:// references"})
        features = requirements.get("features", [])
        if not isinstance(features, list):
            features = []
            unsupported.append({"feature": "feature_input", "workflow": self.platform, "reasons": ["features_must_be_a_list"], "required_action": "provide feature requests with exact commands and evidence references"})
        for feature_request in features:
            if not isinstance(feature_request, dict):
                unsupported.append({"feature": "unidentified_feature", "workflow": self.platform, "reasons": ["feature_request_must_be_an_object"], "required_action": "provide a structured feature request"})
                continue
            result = self.guards.evaluate(feature_request, capability_evidence if isinstance(capability_evidence, dict) else {}, license_evidence if isinstance(license_evidence, dict) else {}, self.platform, str(os_version) if os_version is not None else None, production, default_decisions)
            if not result.allowed:
                unsupported.append(self.guards.unsupported_entry(result, self.platform))
                continue
            commands = [str(command) for command in feature_request["commands"]]
            all_commands.extend(commands)
            capability_ids.extend(result.capability_evidence_ids)
            license_ids.extend(result.license_evidence_ids)
            command_sources.extend(result.command_source_ids)
            decision_ids.extend(result.decision_ids)
        status = "blocked_unsupported_features" if unsupported else "generated"
        if not features and not secret_issues:
            status = "generated_empty_config"
        if unsupported:
            rendered = ""
            all_commands = []
        else:
            rendered = self._render({"schema_version": self.SCHEMA_VERSION, "artifact_id": "pending", "device_id": device_id, "vendor": self.vendor, "platform": self.platform, "os_version": os_version, "commands": all_commands, "secret_references": list(secret_references), "decision_ids": decision_ids})
        artifact = self._artifact(device_id, str(os_version) if os_version is not None else None, status, rendered, all_commands, unsupported, capability_ids, license_ids, command_sources, decision_ids, secret_references)
        decision = self.record_decision("config_generation", status, "Rendered only exact commands that passed capability, license, command-source, secret-reference, and design-decision gates.", alternatives=["fake_command_substitution", "silent_feature_omission"], rejection_reasons={"fake_command_substitution": "would create unsupported configuration claims", "silent_feature_omission": "would hide unsupported features from the audit trail"})
        return GenerationResult(artifact, tuple(self.decisions + [decision]), tuple(self.assumptions))

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """BaseDesigner-compatible entry point returning a serializable artifact."""
        return self.generate(requirements).artifact.to_dict()
