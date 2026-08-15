"""Strict Jinja2 rendering with network-aware filters and audit events."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
from typing import Any

from .models import TemplateAuditEvent
from .template_registry import TemplateRegistry


class TemplateRenderError(RuntimeError):
    """Raised when a template cannot be rendered safely."""


class TemplateRenderer:
    """Render registered templates while retaining validation and evidence lineage."""

    def __init__(self, registry: TemplateRegistry, template_root: str | Path | None = None) -> None:
        self.registry = registry
        self.template_root = Path(template_root or (Path(__file__).parent / "templates"))
        self.audit_events: list[TemplateAuditEvent] = []

    @staticmethod
    def _secret_ref(value: Any) -> str:
        if not isinstance(value, str) or not value.startswith("secret://"):
            raise ValueError("secret filters accept SecretManager references only")
        return value

    @staticmethod
    def _ip_network(value: Any) -> str:
        return str(ipaddress.ip_network(str(value), strict=False))

    @staticmethod
    def _ip_netmask(value: Any) -> str:
        network = ipaddress.ip_network(str(value), strict=False)
        return str(network.netmask)

    @staticmethod
    def _ip_wildcard(value: Any) -> str:
        if isinstance(value, str) and "/" not in value:
            network = ipaddress.ip_network(f"0.0.0.0/{value}", strict=False)
        else:
            network = ipaddress.ip_network(str(value), strict=False)
        wildcard = int(network.hostmask)
        return str(ipaddress.IPv4Address(wildcard))

    @staticmethod
    def _dotted_to_cidr(value: Any) -> int:
        mask = ipaddress.IPv4Network(f"0.0.0.0/{value}").netmask
        return int(mask).bit_count()

    @staticmethod
    def _mac_format(value: Any, separator: str = ".") -> str:
        raw = re.sub(r"[^0-9A-Fa-f]", "", str(value))
        if len(raw) != 12:
            raise ValueError("MAC address must contain twelve hexadecimal digits")
        if separator == ".":
            return ".".join(raw[index:index + 4].lower() for index in range(0, 12, 4))
        return separator.join(raw[index:index + 2].lower() for index in range(0, 12, 2))

    @staticmethod
    def _interface_short(value: Any) -> str:
        text = str(value)
        mappings = (("GigabitEthernet", "Gi"), ("TenGigabitEthernet", "Te"), ("TwentyFiveGigE", "Twe"), ("FortyGigabitEthernet", "Fo"), ("HundredGigE", "Hu"), ("Ethernet", "Eth"), ("Loopback", "Lo"), ("Port-channel", "Po"), ("Port-Channel", "Po"), ("Management", "Mgmt"))
        for long_name, short_name in mappings:
            if text.startswith(long_name):
                return short_name + text[len(long_name):]
        return text

    @staticmethod
    def _interface_long(value: Any) -> str:
        text = str(value)
        mappings = (("Gi", "GigabitEthernet"), ("Te", "TenGigabitEthernet"), ("Twe", "TwentyFiveGigE"), ("Fo", "FortyGigabitEthernet"), ("Hu", "HundredGigE"), ("Eth", "Ethernet"), ("Lo", "Loopback"), ("Po", "Port-channel"), ("Mgmt", "Management"))
        for short_name, long_name in mappings:
            if text.startswith(short_name) and (len(text) == len(short_name) or text[len(short_name)].isdigit()):
                return long_name + text[len(short_name):]
        return text

    @staticmethod
    def _quote_if_spaces(value: Any) -> str:
        text = str(value)
        return f'"{text}"' if any(character.isspace() for character in text) else text

    @staticmethod
    def _is_ipv4(value: Any) -> bool:
        try:
            return ipaddress.ip_address(str(value)).version == 4
        except ValueError:
            return False

    @staticmethod
    def _is_ipv6(value: Any) -> bool:
        try:
            return ipaddress.ip_address(str(value)).version == 6
        except ValueError:
            return False

    @staticmethod
    def _is_cidr(value: Any) -> bool:
        try:
            ipaddress.ip_network(str(value), strict=False)
            return "/" in str(value)
        except ValueError:
            return False

    @staticmethod
    def _is_valid_vlan(value: Any) -> bool:
        return isinstance(value, int) and 1 <= value <= 4094

    @staticmethod
    def _is_valid_asn(value: Any) -> bool:
        return isinstance(value, int) and 1 <= value <= 4294967295

    @staticmethod
    def _find_inline_secrets(value: Any, path: str = "variables") -> list[str]:
        tokens = ("password", "passwd", "secret", "token", "psk", "private_key", "api_key", "community")
        found: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if any(token in str(key).lower() for token in tokens) and isinstance(child, str) and child and not child.startswith("secret://"):
                    found.append(child_path)
                found.extend(TemplateRenderer._find_inline_secrets(child, child_path))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                found.extend(TemplateRenderer._find_inline_secrets(child, f"{path}[{index}]"))
        return found

    def _environment(self) -> Any:
        try:
            from jinja2 import Environment, FileSystemLoader, StrictUndefined
        except ImportError as exc:
            raise TemplateRenderError("Jinja2 is required for template rendering") from exc
        environment = Environment(loader=FileSystemLoader(str(self.template_root)), undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)
        filters = {
            "ip_network": self._ip_network,
            "ip_wildcard": self._ip_wildcard,
            "ip_netmask": self._ip_netmask,
            "ip_hostmask": self._ip_wildcard,
            "cidr_to_netmask": self._ip_netmask,
            "dotted_to_cidr": self._dotted_to_cidr,
            "mac_format": self._mac_format,
            "interface_short": self._interface_short,
            "interface_long": self._interface_long,
            "quote_if_spaces": self._quote_if_spaces,
            "encrypt_type7": self._secret_ref,
            "secret_ref": self._secret_ref,
        }
        environment.filters.update(filters)
        environment.tests.update({"ipv4": self._is_ipv4, "ipv6": self._is_ipv6, "cidr": self._is_cidr, "valid_vlan": self._is_valid_vlan, "valid_asn": self._is_valid_asn})
        return environment

    def _template_name(self, file_path: str) -> str:
        marker = "config_generators/templates/"
        return file_path[len(marker):] if file_path.startswith(marker) else file_path

    def render(self, template_id: str, variables: dict[str, Any], decision_ids: tuple[str, ...] = (), production: bool = False) -> str:
        """Render one registered template and append an audit event."""
        metadata = self.registry.get(template_id)
        if metadata is None:
            raise TemplateRenderError(f"unknown template: {template_id}")
        if production and metadata.validation_state.value != "verified":
            raise TemplateRenderError(f"template {template_id} is not production-validated for a model/version scope")
        inline_secret_paths = self._find_inline_secrets(variables)
        if inline_secret_paths:
            raise TemplateRenderError(f"inline secret values are forbidden: {', '.join(inline_secret_paths)}")
        event_id = hashlib.sha256(f"{template_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16]
        try:
            rendered = self._environment().get_template(self._template_name(metadata.file_path)).render(**variables)
        except Exception as exc:
            self.audit_events.append(TemplateAuditEvent(event_id, template_id, "failed", tuple(sorted(variables)), decision_ids, metadata.evidence_reference, self._secret_refs(variables), str(exc)))
            raise TemplateRenderError(f"template render failed for {template_id}: {exc}") from exc
        self.audit_events.append(TemplateAuditEvent(event_id, template_id, "rendered_preview" if not production else "rendered", tuple(sorted(variables)), decision_ids, metadata.evidence_reference, self._secret_refs(variables), "rendered with strict undefined handling"))
        return rendered

    @staticmethod
    def _secret_refs(value: Any) -> tuple[str, ...]:
        refs: list[str] = []
        if isinstance(value, str) and value.startswith("secret://"):
            refs.append(value)
        elif isinstance(value, dict):
            for child in value.values():
                refs.extend(TemplateRenderer._secret_refs(child))
        elif isinstance(value, list):
            for child in value:
                refs.extend(TemplateRenderer._secret_refs(child))
        return tuple(dict.fromkeys(refs))

    def audit_snapshot(self) -> list[dict[str, Any]]:
        """Return JSON-safe audit events."""
        return [{"event_id": event.event_id, "template_id": event.template_id, "status": event.status, "variable_names": list(event.variable_names), "decision_ids": list(event.decision_ids), "evidence_reference": event.evidence_reference, "secret_references": list(event.secret_references), "message": event.message} for event in self.audit_events]
