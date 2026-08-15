"""Shared vendor interpreter behavior for common show commands."""

from __future__ import annotations

import re
from typing import Any

from .interpreter_engine import InterpreterEngine, ShowInterpretation


class VendorShowInterpreter:
    """Vendor-family parser using explicit bounded regex patterns."""

    vendor = "unknown"
    platform = "unknown"

    def interpret(self, raw_output: str, command: str) -> ShowInterpretation:
        """Parse common output and add vendor-family semantic markers."""
        generic = InterpreterEngine._generic(raw_output, command, self.vendor, self.platform)
        parsed = dict(generic.parsed_data)
        anomalies = list(generic.anomalies)
        indicators = dict(generic.health_indicators)
        lower_command = command.lower()
        if "ospf" in lower_command or "ospf" in raw_output.lower():
            neighbors = re.findall(r"(?im)^\s*([0-9.]+)\s+([A-Za-z0-9/.-]+)\s+(FULL|2WAY|INIT|EXSTART|EXCHANGE|LOADING|DOWN)\b", raw_output)
            if neighbors:
                parsed["ospf_neighbors"] = [{"neighbor_id": item[0], "interface": item[1], "state": item[2]} for item in neighbors]
                if any(item[2].upper() not in {"FULL", "2WAY"} for item in neighbors):
                    anomalies.append("ospf_neighbor_not_full_or_2way")
                    indicators["ospf"] = "degraded"
        if "bgp" in lower_command or "bgp" in raw_output.lower():
            if re.search(r"(?i)established", raw_output):
                indicators["bgp"] = "established_marker_present"
            if re.search(r"(?i)idle|active|connect", raw_output):
                anomalies.append("bgp_peer_not_established_marker")
                indicators["bgp"] = "degraded"
        if "access-list" in lower_command or "firewall" in lower_command or "acl" in lower_command:
            deny_hits = re.findall(r"(?im)^.*\bdeny\b.*?(\d+)\s*$", raw_output)
            parsed["deny_hit_count_markers"] = [int(item) for item in deny_hits]
            if deny_hits:
                anomalies.append("deny_rule_hit_marker")
                indicators["policy"] = "requires_flow_validation"
        if "environment" in lower_command or "power" in lower_command:
            if re.search(r"(?i)fail|fault|critical|overheat|denied", raw_output):
                anomalies.append("environment_or_power_fault_marker")
                indicators["environment"] = "degraded"
        generic.parsed_data = parsed
        generic.anomalies = list(dict.fromkeys(anomalies))
        generic.health_indicators = indicators
        generic.confidence = min(0.9, generic.confidence + 0.15)
        generic.limitations = ["vendor parser uses bounded common patterns; unsupported command semantics remain unverified"]
        return generic
