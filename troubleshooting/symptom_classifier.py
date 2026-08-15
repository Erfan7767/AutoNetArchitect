"""Evidence-bounded symptom classification for troubleshooting sessions."""

from __future__ import annotations

import re
from typing import Any, Mapping

from designers.base_designer import Assumption, DecisionRecord

from .models import SymptomClassification, SymptomInput, SymptomClass


class SymptomClassifier:
    """Classify symptoms without pretending ambiguous language is certainty."""

    TAXONOMY: dict[SymptomClass, dict[str, tuple[str, ...]]] = {
        SymptomClass.CONNECTIVITY_LOSS: {
            "total": ("no connectivity", "cannot reach", "unreachable", "total outage", "لا يوجد اتصال", "لا يمكن الوصول"),
            "partial": ("some destinations", "partial connectivity", "بعض الوجهات"),
            "intermittent": ("intermittent", "goes up and down", "متقطع", "يذهب ويعود"),
            "one_directional": ("one way", "one-directional", "باتجاه واحد"),
        },
        SymptomClass.PERFORMANCE_DEGRADATION: {
            "high_latency": ("latency", "delay", "تأخير"),
            "packet_loss": ("packet loss", "loss", "فقد الحزم"),
            "jitter": ("jitter", "تذبذب"),
            "low_throughput": ("slow throughput", "low bandwidth", "سرعة منخفضة"),
            "application_slow": ("application slow", "التطبيق بطيء"),
        },
        SymptomClass.AUTHENTICATION_FAILURE: {
            "login_failure": ("login failed", "authentication failed", "فشل الدخول", "المصادقة"),
            "intermittent_auth": ("intermittent login", "مصادقة متقطعة"),
            "radius_timeout": ("radius timeout", "radius لا يستجيب"),
            "certificate_error": ("certificate", "شهادة"),
            "vlan_assignment_wrong": ("wrong vlan after auth", "vlan خاطئ بعد المصادقة"),
        },
        SymptomClass.ROUTING_ISSUE: {
            "unreachable": ("route", "routing", "مسار", "توجيه"),
            "suboptimal_path": ("suboptimal", "المسار غير مثالي"),
            "routing_loop": ("routing loop", "حلقة توجيه"),
            "route_flapping": ("flapping", "route flap", "يتذبذب المسار"),
            "asymmetric_routing": ("asymmetric", "غير متماثل"),
        },
        SymptomClass.L2_ISSUE: {
            "broadcast_storm": ("broadcast storm", "عاصفة broadcast"),
            "mac_flapping": ("mac flapping", "يتذبذب mac"),
            "stp_issue": ("stp", "spanning tree", "loop"),
            "vlan_issue": ("vlan", "vlan غير موجود"),
            "trunk_issue": ("trunk", "tagged", "native vlan"),
        },
        SymptomClass.WIRELESS_ISSUE: {
            "no_association": ("cannot associate", "no association", "لا يتصل لاسلكيا"),
            "frequent_disconnection": ("wireless disconnect", "انقطاع لاسلكي"),
            "slow_wireless": ("slow wifi", "wireless slow", "سرعة لاسلكية"),
            "roaming_issue": ("roaming", "التنقل بين ap"),
            "interference": ("interference", "تداخل"),
        },
        SymptomClass.VPN_ISSUE: {
            "tunnel_down": ("vpn tunnel", "tunnel down", "النفق"),
            "phase1_failure": ("phase 1", "ike phase 1"),
            "phase2_failure": ("phase 2", "ipsec phase 2"),
            "traffic_not_encrypted": ("not encrypted", "غير مشفرة"),
            "split_tunnel_issue": ("split tunnel", "split tunneling"),
        },
        SymptomClass.DNS_DHCP_ISSUE: {
            "no_ip_address": ("no ip", "dhcp", "لا يحصل على ip"),
            "wrong_ip": ("wrong ip", "ip خاطئ"),
            "dns_resolution_failure": ("dns", "name resolution", "حل الأسماء"),
            "dns_slow": ("dns slow", "حل الأسماء بطيء"),
        },
        SymptomClass.DEVICE_ISSUE: {
            "high_cpu": ("high cpu", "cpu عالي"),
            "high_memory": ("high memory", "ذاكرة عالية"),
            "process_crash": ("process crash", "crashed", "عملية تحطمت"),
            "hardware_failure": ("hardware failure", "عطل hardware"),
            "power_issue": ("power", "طاقة"),
        },
    }

    WORKFLOWS = {
        SymptomClass.CONNECTIVITY_LOSS: "connectivity_diagnostic",
        SymptomClass.PERFORMANCE_DEGRADATION: "performance_diagnostic",
        SymptomClass.AUTHENTICATION_FAILURE: "authentication_diagnostic",
        SymptomClass.ROUTING_ISSUE: "routing_diagnostic",
        SymptomClass.L2_ISSUE: "l2_diagnostic",
        SymptomClass.WIRELESS_ISSUE: "wireless_diagnostic",
        SymptomClass.VPN_ISSUE: "vpn_diagnostic",
        SymptomClass.DNS_DHCP_ISSUE: "dns_diagnostic",
        SymptomClass.DEVICE_ISSUE: "physical_layer_diagnostic",
        SymptomClass.UNKNOWN: "connectivity_diagnostic",
    }

    def __init__(self) -> None:
        """Initialize the classifier and its audit records."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def classify(self, symptom: SymptomInput | str, structured: Mapping[str, Any] | None = None) -> SymptomClassification:
        """Classify natural-language or structured symptoms."""
        if isinstance(symptom, SymptomInput):
            text = symptom.symptom_description
            context = symptom.additional_context
        else:
            text = symptom
            context = dict(structured or {})
        normalized = text.lower()
        matches: list[tuple[SymptomClass, str, str]] = []
        for category, subtypes in self.TAXONOMY.items():
            for subtype, terms in subtypes.items():
                for term in terms:
                    if term.lower() in normalized:
                        matches.append((category, subtype, term))
        for key, value in context.items():
            category = self._category_from_value(key, value)
            if category is not None:
                matches.append((category, str(key), str(value)))
        if not matches:
            self.assumptions.append(Assumption("symptom_taxonomy_match", "unknown", "the supplied symptom did not match a bounded taxonomy term", True))
            primary = SymptomClass.UNKNOWN
            confidence = 0.15
            subtype = "unknown"
            rationale = "no bounded keyword or structured taxonomy match was found"
            matched_terms: list[str] = []
        else:
            counts: dict[SymptomClass, int] = {}
            for category, _, _ in matches:
                counts[category] = counts.get(category, 0) + 1
            primary = max(counts, key=counts.get)
            subtype = next(item[1] for item in matches if item[0] == primary)
            confidence = min(0.95, 0.45 + (counts[primary] * 0.12) + (0.12 if len(counts) == 1 else 0.0))
            rationale = "classification selected the category with the strongest bounded term match"
            matched_terms = [item[2] for item in matches]
            if len(counts) > 1:
                self.assumptions.append(Assumption("primary_symptom_class", primary.value, "multiple symptom classes matched; secondary classes remain relevant", True))
                confidence = min(confidence, 0.72)
        secondary = [category for category in dict.fromkeys(item[0] for item in matches) if category != primary]
        decision = DecisionRecord("SymptomClassifier", f"symptom-classification:{primary.value}:{subtype}", primary.value, "bounded taxonomy match and explicit structured context", [item.value for item in SymptomClass], {item.value: "not selected by available symptom evidence" for item in SymptomClass if item != primary})
        self.decisions.append(decision)
        return SymptomClassification(primary_class=primary, secondary_classes=secondary, subtype=subtype, confidence=confidence, rationale=rationale, suggested_diagnostic_workflows=[self.WORKFLOWS.get(primary, "connectivity_diagnostic")], matched_terms=matched_terms, assumptions=[item.key for item in self.assumptions], decision_id=decision.decision_id)

    @staticmethod
    def _category_from_value(key: str, value: Any) -> SymptomClass | None:
        """Map structured fields to a taxonomy category without guessing arbitrary values."""
        normalized = f"{key} {value}".lower()
        for category, subtypes in SymptomClassifier.TAXONOMY.items():
            if any(term.lower() in normalized for terms in subtypes.values() for term in terms):
                return category
        return None
