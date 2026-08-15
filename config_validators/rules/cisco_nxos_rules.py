"""cisco_nxos syntax rules."""
from __future__ import annotations

from config_validators.rules.common_rules import CommandRule, ParameterSpec

KNOWN_COMMANDS = {
    "rule_0": CommandRule(r"^hostname\\s+\\S+$", valid_modes=('global',), description='Hostname declaration'),
    "rule_1": CommandRule(r"^service\\s+timestamps\\s+(?:debug|log)\\s+datetime(?:\\s+msec)?$", valid_modes=('global',), description='Service timestamps'),
    "rule_2": CommandRule(r"^logging\\s+(?:host\\s+)?\\S+.*$", valid_modes=('global',), description='Logging configuration'),
    "rule_3": CommandRule(r"^ntp\\s+server\\s+\\S+.*$", valid_modes=('global',), description='NTP server'),
    "rule_4": CommandRule(r"^enable\\s+secret(?:\\s+[589])?\\s+\\S+$", valid_modes=('global',), description='Hashed enable secret'),
    "rule_5": CommandRule(r"^username\\s+\\S+.*$", valid_modes=('global',), description='Local username'),
    "rule_6": CommandRule(r"^aaa\\s+.*$", valid_modes=('global',), description='AAA configuration'),
    "rule_7": CommandRule(r"^snmp-server\\s+.*$", valid_modes=('global',), description='SNMP configuration'),
    "rule_8": CommandRule(r"^banner\\s+.*$", valid_modes=('global',), description='Banner configuration'),
    "rule_9": CommandRule(r"^interface\\s+\\S+$", valid_modes=('global',), description='Interface mode'),
    "rule_10": CommandRule(r"^\\s+(?:description|no\\s+shutdown|shutdown|speed|duplex|mtu|switchport|channel-group|ip\\s+address|ipv6\\s+address|standby|vrrp|hsrp|service-policy|spanning-tree|switchport\\s+access|switchport\\s+trunk|ip\\s+ospf|ip\\s+router|dot1x|authentication|storm-control|ip\\s+dhcp|ip\\s+verify|vrf\\s+forwarding|vrf\\s+member)\\b.*$", valid_modes=('interface', 'global', 'parent'), description='Interface subcommand'),
    "rule_11": CommandRule(r"^router\\s+(?:ospf|eigrp|bgp)\\s+\\d+$", valid_modes=('global',), description='Routing process'),
    "rule_12": CommandRule(r"^\\s+(?:router-id|network|passive-interface|no\\s+passive-interface|redistribute|default-information|maximum-paths|neighbor|distance|timers|area|auto-cost|log-adjacency|maximum-paths)\\b.*$", valid_modes=('routing', 'global', 'parent'), description='Routing subcommand'),
    "rule_13": CommandRule(r"^line\\s+.*$", valid_modes=('global',), description='Line mode'),
    "rule_14": CommandRule(r"^\\s+(?:login|transport\\s+input|exec-timeout|logging\\s+synchronous|password|authorization)\\b.*$", valid_modes=('line', 'global', 'parent'), description='Line subcommand'),
    "rule_15": CommandRule(r"^ip\\s+(?:route|access-list|prefix-list|sla|nat|vrf|radius|ssh|domain)\\b.*$", valid_modes=('global',), description='IP feature'),
    "rule_16": CommandRule(r"^(?:access-list|route-map|ip\\s+prefix-list)\\s+.*$", valid_modes=('global',), description='Policy object'),
    "rule_17": CommandRule(r"^vlan\\s+\\d+$", valid_modes=('global',), description='VLAN declaration'),
    "rule_18": CommandRule(r"^\\s+(?:name|state|description)\\s+.*$", valid_modes=('global', 'parent'), description='VLAN subcommand'),
    "rule_19": CommandRule(r"^(?:spanning-tree|feature|vrf\\s+context|vpc|class-map|policy-map|service-policy)\\s+.*$", valid_modes=('global',), description='Platform feature'),
    "rule_20": CommandRule(r"^(?:exit|end|quit|return)$", valid_modes=('global',), description='Mode transition'),
    "rule_21": CommandRule(r"^feature\\s+\\S+$", valid_modes=('global',), description='NX-OS feature'),
}
FORBIDDEN_PATTERNS = []
