"""Section registry for standardized network documentation structures."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .doc_models import ContentType, DocumentSection, DocumentType, SectionStatus


class DocumentSectionRegistry:
    """Register, customize, and resolve ordered sections per document type."""

    def __init__(self) -> None:
        """Initialize standard structures."""
        self._sections: dict[DocumentType, list[DocumentSection]] = {document_type: self._default_sections(document_type) for document_type in DocumentType}

    def get(self, document_type: DocumentType | str) -> tuple[DocumentSection, ...]:
        """Return sections ordered by their order value."""
        selected = DocumentType(document_type)
        return tuple(sorted((item.model_copy(deep=True) for item in self._sections[selected]), key=lambda item: (item.order, item.section_id)))

    def set_sections(self, document_type: DocumentType | str, sections: Iterable[DocumentSection]) -> None:
        """Replace a document structure with validated sections."""
        selected = DocumentType(document_type)
        values = list(sections)
        if not values:
            raise ValueError("a document must have at least one section")
        self._sections[selected] = values

    def add_custom(self, document_type: DocumentType | str, section: DocumentSection) -> None:
        """Append a custom section with a deterministic order."""
        selected = DocumentType(document_type)
        current = list(self.get(selected))
        if any(item.section_id == section.section_id for item in current):
            raise ValueError(f"section already exists: {section.section_id}")
        section = section.model_copy(update={"order": max((item.order for item in current), default=0) + 1})
        current.append(section)
        self._sections[selected] = current

    def reorder(self, document_type: DocumentType | str, ordered_ids: list[str]) -> None:
        """Reorder known sections and keep unspecified sections after them."""
        selected = DocumentType(document_type)
        current = {item.section_id: item for item in self.get(selected)}
        unknown = [item for item in ordered_ids if item not in current]
        if unknown:
            raise KeyError(f"unknown section ids: {unknown}")
        ordered = [current[item] for item in ordered_ids]
        ordered.extend(item for section_id, item in current.items() if section_id not in ordered_ids)
        self._sections[selected] = [item.model_copy(update={"order": index}) for index, item in enumerate(ordered)]

    def mark_not_applicable(self, document_type: DocumentType | str, section_id: str, reason: str) -> None:
        """Mark one section not applicable with an explicit reason."""
        if not reason.strip():
            raise ValueError("not-applicable reason is mandatory")
        selected = DocumentType(document_type)
        updated = []
        for item in self.get(selected):
            updated.append(item.model_copy(update={"status": SectionStatus.NOT_APPLICABLE, "pending_reason": reason} if item.section_id == section_id else {}))
        if not any(item.section_id == section_id for item in updated):
            raise KeyError(section_id)
        self._sections[selected] = updated

    def load_templates(self, template_dir: str | Path) -> list[str]:
        """Validate available JSON templates and return loaded filenames.

        Templates may carry metadata or an explicit list of sections. When a template
        has no explicit section records, the standard in-code structure remains the
        authoritative default rather than being replaced by an empty structure.
        """
        directory = Path(template_dir)
        loaded: list[str] = []
        if not directory.exists():
            return loaded
        for path in sorted(directory.glob("*_template.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("schema_version") is None:
                raise ValueError(f"invalid documentation template: {path.name}")
            loaded.append(path.name)
        return loaded

    @staticmethod
    def _default_sections(document_type: DocumentType) -> list[DocumentSection]:
        """Build a bounded standard structure for one document type."""
        common = [
            DocumentSection(section_id="document_control", section_title_en="Document Control", section_title_ar="ضبط الوثيقة", section_level=1, content_type=ContentType.MIXED, data_source="project_metadata", mandatory=True, order=1),
            DocumentSection(section_id="scope_and_conventions", section_title_en="Scope and Conventions", section_title_ar="النطاق والاصطلاحات", section_level=1, content_type=ContentType.TEXT, data_source="project_metadata", mandatory=True, order=2),
            DocumentSection(section_id="source_basis", section_title_en="Source of Truth and Evidence Basis", section_title_ar="أساس مصدر الحقيقة والأدلة", section_level=1, content_type=ContentType.TABLE, data_source="sot_basis", mandatory=True, order=3),
        ]
        section_map: dict[DocumentType, list[DocumentSection]] = {
            DocumentType.HLD: [DocumentSection(section_id="executive_summary", section_title_en="Executive Summary", section_title_ar="الملخص التنفيذي", section_level=1, content_type=ContentType.TEXT, data_source="requirements", mandatory=True, order=4), DocumentSection(section_id="logical_architecture", section_title_en="Logical Architecture", section_title_ar="المعمارية المنطقية", section_level=1, content_type=ContentType.MIXED, data_source="design", mandatory=True, order=5), DocumentSection(section_id="security_architecture", section_title_en="Security Architecture", section_title_ar="معمارية الأمن", section_level=1, content_type=ContentType.MIXED, data_source="security_design", mandatory=True, order=6), DocumentSection(section_id="equipment_summary", section_title_en="Equipment Summary", section_title_ar="ملخص المعدات", section_level=1, content_type=ContentType.TABLE, data_source="equipment", mandatory=True, order=7), DocumentSection(section_id="risks_and_assumptions", section_title_en="Risks and Assumptions", section_title_ar="المخاطر والافتراضات", section_level=1, content_type=ContentType.TABLE, data_source="governance", mandatory=True, order=8)],
            DocumentType.LLD: [DocumentSection(section_id="site_detail", section_title_en="Per-Site Design Detail", section_title_ar="تفاصيل التصميم لكل موقع", section_level=1, content_type=ContentType.MIXED, data_source="physical_design", mandatory=True, order=4), DocumentSection(section_id="interface_assignment", section_title_en="Interface Assignment", section_title_ar="توزيع الواجهات", section_level=1, content_type=ContentType.TABLE, data_source="interface_assignment", mandatory=True, order=5), DocumentSection(section_id="addressing_detail", section_title_en="IP and VLAN Detail", section_title_ar="تفاصيل IP وVLAN", section_level=1, content_type=ContentType.TABLE, data_source="ip_design", mandatory=True, order=6), DocumentSection(section_id="routing_and_security", section_title_en="Routing and Security Detail", section_title_ar="تفاصيل التوجيه والأمن", section_level=1, content_type=ContentType.MIXED, data_source="routing_security", mandatory=True, order=7), DocumentSection(section_id="device_configurations", section_title_en="Device Configurations", section_title_ar="تهيئات الأجهزة", section_level=1, content_type=ContentType.MIXED, data_source="config_artifacts", mandatory=True, order=8)],
            DocumentType.IP_ADDRESS_PLAN: [DocumentSection(section_id="subnets", section_title_en="Subnet Allocation", section_title_ar="توزيع الشبكات الفرعية", section_level=1, content_type=ContentType.TABLE, data_source="ip_design", mandatory=True, order=4), DocumentSection(section_id="loopbacks", section_title_en="Loopbacks", section_title_ar="عناوين Loopback", section_level=1, content_type=ContentType.TABLE, data_source="ip_design", mandatory=False, order=5), DocumentSection(section_id="management", section_title_en="Management Addressing", section_title_ar="عنونة الإدارة", section_level=1, content_type=ContentType.TABLE, data_source="ip_design", mandatory=True, order=6)],
            DocumentType.VLAN_DATABASE: [DocumentSection(section_id="vlan_table", section_title_en="VLAN Database", section_title_ar="قاعدة بيانات VLAN", section_level=1, content_type=ContentType.TABLE, data_source="vlan_design", mandatory=True, order=4)],
            DocumentType.PORT_MAPPING: [DocumentSection(section_id="port_table", section_title_en="Port Mapping Matrix", section_title_ar="مصفوفة توزيع المنافذ", section_level=1, content_type=ContentType.TABLE, data_source="interface_assignment", mandatory=True, order=4)],
            DocumentType.CABLE_SCHEDULE: [DocumentSection(section_id="cable_table", section_title_en="Cable Schedule", section_title_ar="جدول الكابلات", section_level=1, content_type=ContentType.TABLE, data_source="physical_design", mandatory=True, order=4)],
            DocumentType.ROUTING_DESIGN: [DocumentSection(section_id="routing_protocols", section_title_en="Routing Protocols", section_title_ar="بروتوكولات التوجيه", section_level=1, content_type=ContentType.MIXED, data_source="routing_design", mandatory=True, order=4), DocumentSection(section_id="routing_tables", section_title_en="Routing Tables and Policies", section_title_ar="جداول وسياسات التوجيه", section_level=1, content_type=ContentType.TABLE, data_source="routing_design", mandatory=True, order=5)],
            DocumentType.FIREWALL_RULE_MATRIX: [DocumentSection(section_id="firewall_rules", section_title_en="Firewall Rules", section_title_ar="قواعد الجدار الناري", section_level=1, content_type=ContentType.TABLE, data_source="security_design", mandatory=True, order=4)],
            DocumentType.ACL_DOCUMENTATION: [DocumentSection(section_id="acl_rules", section_title_en="ACL Rules", section_title_ar="قواعد ACL", section_level=1, content_type=ContentType.TABLE, data_source="security_design", mandatory=True, order=4)],
            DocumentType.NAT_DOCUMENTATION: [DocumentSection(section_id="nat_rules", section_title_en="NAT Rules", section_title_ar="قواعد NAT", section_level=1, content_type=ContentType.TABLE, data_source="nat_design", mandatory=True, order=4)],
            DocumentType.WIRELESS_DESIGN: [DocumentSection(section_id="wireless_architecture", section_title_en="Wireless Architecture", section_title_ar="معمارية الشبكة اللاسلكية", section_level=1, content_type=ContentType.MIXED, data_source="wireless_design", mandatory=True, order=4), DocumentSection(section_id="survey_status", section_title_en="Survey and RF Evidence Status", section_title_ar="حالة المسح وأدلة RF", section_level=1, content_type=ContentType.TABLE, data_source="wireless_evidence", mandatory=True, order=5)],
            DocumentType.QOS_DESIGN: [DocumentSection(section_id="qos_policies", section_title_en="QoS Policies", section_title_ar="سياسات QoS", section_level=1, content_type=ContentType.TABLE, data_source="qos_design", mandatory=True, order=4)],
            DocumentType.SECURITY_DESIGN: [DocumentSection(section_id="zones_and_controls", section_title_en="Zones and Security Controls", section_title_ar="المناطق وضوابط الأمن", section_level=1, content_type=ContentType.MIXED, data_source="security_design", mandatory=True, order=4)],
            DocumentType.WAN_DESIGN: [DocumentSection(section_id="wan_links", section_title_en="WAN Links and Handoffs", section_title_ar="وصلات وتسليمات WAN", section_level=1, content_type=ContentType.TABLE, data_source="wan_design", mandatory=True, order=4)],
            DocumentType.VPN_DESIGN: [DocumentSection(section_id="vpn_tunnels", section_title_en="VPN Tunnels", section_title_ar="أنفاق VPN", section_level=1, content_type=ContentType.TABLE, data_source="vpn_design", mandatory=True, order=4)],
            DocumentType.DR_PLAN: [DocumentSection(section_id="dr_strategy", section_title_en="DR Strategy", section_title_ar="استراتيجية التعافي من الكوارث", section_level=1, content_type=ContentType.MIXED, data_source="dr_design", mandatory=True, order=4), DocumentSection(section_id="recovery_targets", section_title_en="RPO and RTO", section_title_ar="أهداف RPO وRTO", section_level=1, content_type=ContentType.TABLE, data_source="dr_design", mandatory=True, order=5)],
            DocumentType.PHYSICAL_LAYOUT: [DocumentSection(section_id="site_layout", section_title_en="Site Layout", section_title_ar="مخطط الموقع", section_level=1, content_type=ContentType.MIXED, data_source="physical_design", mandatory=True, order=4), DocumentSection(section_id="racks_and_pathways", section_title_en="Racks and Cable Pathways", section_title_ar="الرفوف ومسارات الكابلات", section_level=1, content_type=ContentType.TABLE, data_source="physical_design", mandatory=True, order=5)],
            DocumentType.EQUIPMENT_INVENTORY: [DocumentSection(section_id="equipment_table", section_title_en="Equipment Inventory", section_title_ar="جرد المعدات", section_level=1, content_type=ContentType.TABLE, data_source="equipment", mandatory=True, order=4)],
            DocumentType.BOM: [DocumentSection(section_id="bom_table", section_title_en="Bill of Materials", section_title_ar="جدول المواد", section_level=1, content_type=ContentType.TABLE, data_source="bom", mandatory=True, order=4), DocumentSection(section_id="bom_limitations", section_title_en="BOM Assumptions and Limitations", section_title_ar="افتراضات وقيود BOM", section_level=1, content_type=ContentType.TEXT, data_source="bom", mandatory=True, order=5)],
            DocumentType.SOW: [DocumentSection(section_id="scope_of_work", section_title_en="Scope of Work", section_title_ar="نطاق العمل", section_level=1, content_type=ContentType.MIXED, data_source="sow", mandatory=True, order=4), DocumentSection(section_id="responsibilities", section_title_en="Responsibilities and Acceptance", section_title_ar="المسؤوليات والقبول", section_level=1, content_type=ContentType.TABLE, data_source="sow", mandatory=True, order=5)],
            DocumentType.ATP: [DocumentSection(section_id="test_objectives", section_title_en="Test Objectives", section_title_ar="أهداف الاختبار", section_level=1, content_type=ContentType.TEXT, data_source="atp", mandatory=True, order=4), DocumentSection(section_id="test_cases", section_title_en="Test Cases", section_title_ar="حالات الاختبار", section_level=1, content_type=ContentType.TABLE, data_source="atp", mandatory=True, order=5), DocumentSection(section_id="signoff", section_title_en="Sign-Off", section_title_ar="التوقيع والاعتماد", section_level=1, content_type=ContentType.TABLE, data_source="atp", mandatory=True, order=6)],
            DocumentType.AS_BUILT: [DocumentSection(section_id="actual_state", section_title_en="Actual State", section_title_ar="الحالة الفعلية", section_level=1, content_type=ContentType.MIXED, data_source="as_built", mandatory=True, order=4), DocumentSection(section_id="deviations", section_title_en="Design Deviations", section_title_ar="الانحرافات عن التصميم", section_level=1, content_type=ContentType.TABLE, data_source="as_built", mandatory=True, order=5), DocumentSection(section_id="verification_results", section_title_en="Verification Results", section_title_ar="نتائج التحقق", section_level=1, content_type=ContentType.TABLE, data_source="operational_state", mandatory=True, order=6)],
            DocumentType.HANDOVER_PACK: [DocumentSection(section_id="document_index", section_title_en="Document Index", section_title_ar="فهرس الوثائق", section_level=1, content_type=ContentType.TABLE, data_source="handover", mandatory=True, order=4), DocumentSection(section_id="acceptance_actions", section_title_en="Acceptance Actions", section_title_ar="إجراءات القبول", section_level=1, content_type=ContentType.LIST, data_source="handover", mandatory=True, order=5)],
            DocumentType.OPERATIONAL_RUNBOOK: [DocumentSection(section_id="network_overview", section_title_en="Network Overview", section_title_ar="نظرة عامة على الشبكة", section_level=1, content_type=ContentType.MIXED, data_source="operational_state", mandatory=True, order=4), DocumentSection(section_id="standard_procedures", section_title_en="Standard Operating Procedures", section_title_ar="إجراءات التشغيل القياسية", section_level=1, content_type=ContentType.LIST, data_source="operations", mandatory=True, order=5), DocumentSection(section_id="emergency_procedures", section_title_en="Emergency Procedures", section_title_ar="إجراءات الطوارئ", section_level=1, content_type=ContentType.LIST, data_source="incident_response", mandatory=True, order=6)],
            DocumentType.TROUBLESHOOTING_GUIDE: [DocumentSection(section_id="symptoms", section_title_en="Common Symptoms and Diagnostic Paths", section_title_ar="الأعراض ومسارات التشخيص", section_level=1, content_type=ContentType.MIXED, data_source="troubleshooting", mandatory=True, order=4), DocumentSection(section_id="vendor_commands", section_title_en="Vendor Read-Only Commands", section_title_ar="أوامر القراءة حسب الشركة", section_level=1, content_type=ContentType.TABLE, data_source="troubleshooting", mandatory=True, order=5)],
            DocumentType.CHANGE_PROCEDURE: [DocumentSection(section_id="change_steps", section_title_en="Change Steps", section_title_ar="خطوات التغيير", section_level=1, content_type=ContentType.LIST, data_source="change_management", mandatory=True, order=4), DocumentSection(section_id="rollback_and_verification", section_title_en="Rollback and Verification", section_title_ar="الاسترجاع والتحقق", section_level=1, content_type=ContentType.MIXED, data_source="change_management", mandatory=True, order=5)],
            DocumentType.COMPLIANCE_REPORT: [DocumentSection(section_id="compliance_scope", section_title_en="Compliance Scope", section_title_ar="نطاق الامتثال", section_level=1, content_type=ContentType.TEXT, data_source="compliance", mandatory=True, order=4), DocumentSection(section_id="control_assessments", section_title_en="Control Assessments", section_title_ar="تقييمات الضوابط", section_level=1, content_type=ContentType.TABLE, data_source="compliance", mandatory=True, order=5)],
            DocumentType.NETWORK_INVENTORY: [DocumentSection(section_id="inventory_table", section_title_en="Network Inventory", section_title_ar="جرد الشبكة", section_level=1, content_type=ContentType.TABLE, data_source="inventory", mandatory=True, order=4)],
            DocumentType.DECISION_LOG: [DocumentSection(section_id="decisions", section_title_en="Design Decisions", section_title_ar="قرارات التصميم", section_level=1, content_type=ContentType.TABLE, data_source="decisions", mandatory=True, order=4)],
            DocumentType.ASSUMPTION_REGISTER: [DocumentSection(section_id="assumptions", section_title_en="Assumptions", section_title_ar="الافتراضات", section_level=1, content_type=ContentType.TABLE, data_source="assumptions", mandatory=True, order=4)],
            DocumentType.RISK_REGISTER: [DocumentSection(section_id="risks", section_title_en="Risks", section_title_ar="المخاطر", section_level=1, content_type=ContentType.TABLE, data_source="risks", mandatory=True, order=4)],
            DocumentType.VOICE_DESIGN: [DocumentSection(section_id="voice_architecture", section_title_en="Voice Architecture", section_title_ar="معمارية الصوت", section_level=1, content_type=ContentType.MIXED, data_source="voice_design", mandatory=True, order=4), DocumentSection(section_id="voice_qos", section_title_en="Voice QoS", section_title_ar="جودة خدمة الصوت", section_level=1, content_type=ContentType.TABLE, data_source="qos_design", mandatory=True, order=5)],
            DocumentType.NAC_DESIGN: [DocumentSection(section_id="nac_architecture", section_title_en="NAC Architecture", section_title_ar="معمارية NAC", section_level=1, content_type=ContentType.MIXED, data_source="nac_design", mandatory=True, order=4), DocumentSection(section_id="identity_flows", section_title_en="Identity and Access Flows", section_title_ar="تدفقات الهوية والوصول", section_level=1, content_type=ContentType.TABLE, data_source="nac_design", mandatory=True, order=5)],
            DocumentType.CAPACITY_REPORT: [DocumentSection(section_id="capacity_state", section_title_en="Current Capacity", section_title_ar="السعة الحالية", section_level=1, content_type=ContentType.TABLE, data_source="traffic_analysis", mandatory=True, order=4), DocumentSection(section_id="capacity_forecast", section_title_en="Growth Forecast and Upgrades", section_title_ar="توقع النمو والترقيات", section_level=1, content_type=ContentType.MIXED, data_source="traffic_analysis", mandatory=True, order=5)],
        }
        return common + section_map.get(document_type, [DocumentSection(section_id="document_content", section_title_en="Document Content", section_title_ar="محتوى الوثيقة", section_level=1, content_type=ContentType.MIXED, data_source="source_artifacts", mandatory=True, order=4)])
