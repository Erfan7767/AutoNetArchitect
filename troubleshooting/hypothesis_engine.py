"""Generate and evaluate evidence-bounded troubleshooting hypotheses."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord

from .models import EvidenceCollection, Hypothesis, HypothesisEvaluation, SymptomClassification, SymptomClass, VerificationStep


class HypothesisEngine:
    """Generate ordered hypotheses and score them only against supplied evidence."""

    BASE_LIBRARY: dict[SymptomClass, tuple[tuple[str, str, str, str], ...]] = {
        SymptomClass.CONNECTIVITY_LOSS: (
            ("physical_link", "physical link down or degraded", "L1", "check interface status, optics, and cable evidence"),
            ("port_disabled", "port administratively disabled or errdisabled", "L1/L2", "verify interface configuration and errdisable cause"),
            ("stp_blocking", "STP is blocking the required path", "L2", "inspect STP state, root, and guard events"),
            ("vlan_mismatch", "VLAN is absent, pruned, or assigned incorrectly", "L2", "compare VLAN and trunk state with design"),
            ("ip_misconfiguration", "IP address or subnet mask is inconsistent", "L3", "compare address state with the IP design"),
            ("gateway_issue", "default gateway or FHRP state is unavailable", "L3", "check ARP and gateway/FHRP evidence"),
            ("acl_blocking", "ACL or firewall policy is blocking traffic", "L3/L4", "inspect applied policy and counters"),
            ("routing_issue", "route or next-hop is missing or unsafe", "L3", "inspect routing table and protocol adjacency"),
            ("nat_issue", "NAT translation or exemption is incorrect", "L3/L4", "inspect translations and intended NAT policy"),
            ("upstream_failure", "an upstream dependency is unavailable", "L1-L3", "correlate neighboring device evidence"),
        ),
        SymptomClass.PERFORMANCE_DEGRADATION: (
            ("congestion", "link or queue congestion is reducing service quality", "L1-L4", "compare utilization, drops, and QoS counters"),
            ("physical_errors", "physical errors are causing retransmission or loss", "L1", "inspect CRC, optical, duplex, and cable evidence"),
            ("qos_policy", "QoS classification or shaping is affecting the flow", "L2-L4", "inspect policy counters and queue state"),
            ("path_latency", "the selected path has excessive latency", "L3", "compare path hops and timing evidence"),
            ("application_dependency", "an application dependency is slow or unavailable", "L7", "requires application-side evidence; network conclusion is bounded"),
        ),
        SymptomClass.AUTHENTICATION_FAILURE: (
            ("credential_or_policy", "credentials or authentication policy reject the request", "L7", "inspect sanitized authentication events"),
            ("radius_unavailable", "RADIUS/AAA service is unavailable or timing out", "L7", "check AAA reachability and timeout evidence"),
            ("certificate_validation", "certificate chain, time, or identity validation fails", "L7", "inspect certificate metadata and clock state"),
            ("authorization_assignment", "authentication succeeds but authorization assignment is wrong", "L2-L7", "compare assigned VLAN/role with policy"),
        ),
        SymptomClass.ROUTING_ISSUE: (
            ("missing_route", "the destination route is absent", "L3", "inspect route table and protocol advertisements"),
            ("adjacency_down", "routing protocol adjacency is not established", "L3", "inspect neighbor state and timers"),
            ("route_filtering", "policy filters the expected route", "L3", "inspect route-map, prefix-list, and policy counters"),
            ("asymmetric_path", "forward and return paths are inconsistent", "L3", "compare path evidence in both directions"),
            ("routing_loop", "the path contains a loop or unstable next-hop", "L3", "inspect TTL, traceroute, and route changes"),
        ),
        SymptomClass.L2_ISSUE: (
            ("vlan_absent", "the VLAN is absent from one or more switches", "L2", "inspect VLAN database and allowed lists"),
            ("trunk_pruned", "the VLAN is not allowed across a trunk", "L2", "compare trunk allowed VLANs with design"),
            ("mac_flapping", "a MAC address is learned on multiple ports", "L2", "inspect MAC learning and topology events"),
            ("native_vlan_mismatch", "native VLAN semantics differ across a trunk", "L2", "inspect native VLAN and tagging state"),
        ),
        SymptomClass.WIRELESS_ISSUE: (
            ("association_failure", "client association or authentication fails", "L2-L7", "inspect AP/controller client and AAA evidence"),
            ("rf_interference", "interference or channel contention degrades service", "L1/L2", "requires survey or controller RF evidence"),
            ("roaming_policy", "roaming or mobility policy is inconsistent", "L2-L7", "inspect client transitions and policy state"),
        ),
        SymptomClass.VPN_ISSUE: (
            ("ike_phase1", "IKE phase 1 negotiation fails", "L3-L7", "compare proposals, identity, and peer reachability"),
            ("ipsec_phase2", "IPsec phase 2 or proxy identity negotiation fails", "L3-L7", "compare transforms, selectors, and PFS"),
            ("vpn_routing", "traffic is not routed into the tunnel", "L3", "inspect routes and tunnel selectors"),
            ("vpn_nat", "NAT changes traffic that should be exempt", "L3/L4", "inspect NAT exemption and translations"),
        ),
        SymptomClass.DNS_DHCP_ISSUE: (
            ("dhcp_unavailable", "DHCP service or relay path is unavailable", "L2-L7", "inspect relay, scope, and server reachability"),
            ("dhcp_scope", "DHCP scope is exhausted or returns wrong options", "L7", "inspect scope and option evidence"),
            ("dns_unavailable", "DNS server or forwarding path is unavailable", "L7", "inspect resolver reachability and response codes"),
            ("dns_policy", "DNS policy or split-horizon behavior is unexpected", "L7", "compare intended and observed resolver policy"),
        ),
        SymptomClass.DEVICE_ISSUE: (
            ("resource_exhaustion", "CPU or memory resource exhaustion affects operation", "L1-L7", "inspect resource and process evidence"),
            ("hardware_failure", "hardware, power, or thermal fault affects operation", "L1", "inspect environment and hardware evidence"),
            ("software_crash", "a process or software defect affects operation", "L7", "inspect crash and version evidence"),
        ),
    }

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def generate(self, classification: SymptomClassification, *, recent_changes: Iterable[Mapping[str, Any]] = (), known_issues: Iterable[Mapping[str, Any]] = ()) -> list[Hypothesis]:
        """Generate ordered hypotheses with bounded probability scores."""
        templates = self.BASE_LIBRARY.get(classification.primary_class, self.BASE_LIBRARY[SymptomClass.CONNECTIVITY_LOSS])
        change_count = len(tuple(recent_changes))
        known_count = len(tuple(known_issues))
        hypotheses: list[Hypothesis] = []
        for index, (hypothesis_id, description, layer, resolution) in enumerate(templates, start=1):
            score = min(0.7, 0.28 + max(0, 8 - index) * 0.035)
            if change_count and index <= 3:
                score = min(0.82, score + 0.1)
            if known_count and index == 1:
                score = min(0.9, score + 0.14)
            step = VerificationStep(step_id=f"{hypothesis_id}:verify", description=f"verify evidence relevant to {description}", commands=[], expected_pattern="structured evidence or read-only show output", interpretation="support or contradiction depends on supplied evidence", read_only=True, order=1)
            hypotheses.append(Hypothesis(hypothesis_id=f"{classification.primary_class.value}:{hypothesis_id}", description=description, probability_score=round(score, 3), verification_steps=[step], required_evidence=[resolution], affects_layer=layer, typical_resolution=resolution, rationale="bounded symptom library ordering; score is not a confirmed probability"))
        hypotheses.sort(key=lambda item: item.probability_score, reverse=True)
        self.decisions.append(DecisionRecord("HypothesisEngine", f"hypotheses:{classification.primary_class.value}", [item.hypothesis_id for item in hypotheses], "ordered by bounded symptom prior, recent-change signal, and known-issue signal", ["static_order", "change_weighted", "known_issue_weighted"], {"static_order": "not selected when evidence signals exist", "change_weighted": "selected when recent change evidence exists", "known_issue_weighted": "selected when a known issue match exists"}))
        if not recent_changes and not known_issues:
            self.assumptions.append(Assumption("hypothesis_context", "no_recent_change_or_known_issue_data", "hypothesis ordering does not infer absent change or advisory data", True))
        return hypotheses

    def evaluate(self, hypothesis: Hypothesis, evidence: EvidenceCollection) -> HypothesisEvaluation:
        """Evaluate a hypothesis by matching evidence text and parsed fields."""
        support: list[str] = []
        contradict: list[str] = []
        missing: list[str] = []
        terms = set(hypothesis.description.lower().split()) | set(hypothesis.hypothesis_id.lower().split(":"))
        for item in evidence.items:
            haystack = f"{item.raw_data} {item.parsed_data} {item.notes}".lower()
            if any(term and term in haystack for term in terms if len(term) > 3):
                if any(marker in haystack for marker in ("down", "fail", "error", "blocked", "mismatch", "drop", "deny", "crc", "timeout")):
                    support.append(item.evidence_id)
                else:
                    contradict.append(item.evidence_id)
        for required in hypothesis.required_evidence:
            if not any(required.lower().split()[0] in f"{item.raw_data} {item.parsed_data}".lower() for item in evidence.items):
                missing.append(required)
        support_score = min(1.0, 0.35 + (0.25 * len(support)) - (0.1 * len(contradict))) if support else 0.15
        confidence = min(0.95, support_score) if not missing else min(0.65, support_score)
        status = "supported" if support and not contradict else "contradicted" if contradict and not support else "inconclusive"
        rationale = "supporting evidence matched bounded indicators" if support else "available evidence did not confirm this hypothesis"
        return HypothesisEvaluation(hypothesis_id=hypothesis.hypothesis_id, status=status, support_score=round(support_score, 3), supporting_evidence_ids=support, contradicting_evidence_ids=contradict, missing_evidence=missing, rationale=rationale, confidence=round(confidence, 3))
