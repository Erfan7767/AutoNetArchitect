"""Mandatory configuration section checks."""
from __future__ import annotations

import re

from .models import Severity, ValidationDiagnostic, ValidationStage


class CompletenessChecker:
    """Report missing policy-required sections without claiming universal readiness."""

    MANDATORY: dict[str, tuple[tuple[str, str, str], ...]] = {
        "cisco_ios_xe": (
            ("hostname", r"^hostname\s+", "cisco_ios_xe.hostname_domain"),
            ("logging", r"^logging(?:\s+host)?\s+", "cisco_ios_xe.logging"),
            ("ntp", r"^ntp\s+server\s+", "cisco_ios_xe.ntp"),
            ("vty", r"^line\s+vty\s+", "cisco_ios_xe.line_vty"),
            ("console", r"^line\s+console\s+", "cisco_ios_xe.line_console"),
            ("enable_secret", r"^enable\s+secret\s+", "cisco_ios_xe.enable_secret"),
        ),
        "cisco_ios": (("hostname", r"^hostname\s+", "cisco_ios.hostname_domain"), ("logging", r"^logging\s+", "cisco_ios.logging"), ("ntp", r"^ntp\s+server\s+", "cisco_ios.ntp"), ("vty", r"^line\s+vty\s+", "cisco_ios.line_vty"), ("console", r"^line\s+console\s+", "cisco_ios.line_console"), ("enable_secret", r"^enable\s+secret\s+", "cisco_ios.enable_secret")),
        "cisco_nxos": (("hostname", r"^hostname\s+", "cisco_nxos.hostname_domain"), ("logging", r"^logging\s+", "cisco_nxos.logging"), ("ntp", r"^ntp\s+server\s+", "cisco_nxos.ntp")),
        "fortinet": (("system_global", r"^config\s+system\s+global$", "fortinet.base_system"), ("admin_user", r"^config\s+system\s+admin$", "fortinet.admin_users"), ("interfaces", r"^config\s+system\s+interface$", "fortinet.interfaces"), ("default_route", r"^config\s+router\s+static$", "fortinet.static_routes")),
        "paloalto": (("hostname", r"^set\s+deviceconfig\s+system\s+hostname\s+", "paloalto.hostname_dns"), ("security_policy", r"^set\s+rulebase\s+security\s+rules\s+", "paloalto.security_policy")),
        "huawei": (("sysname", r"^sysname\s+", "huawei.hostname_domain"), ("logging", r"^info-center\s+", "huawei.logging"), ("ntp", r"^ntp-service\s+unicast-server\s+", "huawei.ntp")),
        "aruba_aoscx": (("hostname", r"^hostname\s+", "aruba_aoscx.hostname_dns"), ("logging", r"^logging\s+", "aruba_aoscx.logging"), ("ntp", r"^ntp\s+server\s+", "aruba_aoscx.ntp")),
        "juniper_junos": (("hostname", r"^set\s+system\s+host-name\s+", "juniper_junos.hostname_dns"), ("ntp", r"^set\s+system\s+ntp\s+server\s+", "juniper_junos.ntp")),
        "mikrotik_routeros": (("identity", r"^/system\s+identity\s+set\s+", "mikrotik_routeros.identity_dns"), ("ntp", r"^/system\s+ntp\s+client\s+set\s+", "mikrotik_routeros.ntp")),
    }

    def check(self, config_text: str, vendor: str, platform: str, policy: dict[str, bool] | None = None) -> list[ValidationDiagnostic]:
        """Return warnings for missing configured mandatory sections."""
        key = f"{vendor}_{platform}".lower().replace(" ", "_").replace("-", "_")
        key = {"fortinet_fortios": "fortinet", "palo_alto_networks_pan_os": "paloalto", "aruba_aos_cx": "aruba_aoscx", "cisco_nx_os": "cisco_nxos", "mikrotik_routeros": "mikrotik_routeros"}.get(key, key)
        lines = config_text.splitlines()
        diagnostics: list[ValidationDiagnostic] = []
        for section, pattern, template in self.MANDATORY.get(key, ()):
            if policy and policy.get(section) is False:
                continue
            if not any(re.search(pattern, line.strip(), re.I) for line in lines):
                diagnostics.append(ValidationDiagnostic("MISSING_MANDATORY_SECTION", f"Mandatory section {section!r} was not found for this validator policy.", Severity.WARNING, ValidationStage.COMPLETENESS, remediation=f"Supply the required design decision or render {template}.", metadata={"section_name": section, "suggested_template": template, "reason_mandatory": "vendor baseline policy"}))
        return diagnostics
