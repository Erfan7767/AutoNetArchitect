from change_management import ChangeRequest, ChangeTemplateLibrary


def test_change_template_library_contains_required_templates_and_applies_skeleton():
    library = ChangeTemplateLibrary()
    assert {template.template_id for template in library.list()} == {"add_vlan", "add_access_port", "modify_acl", "add_static_route", "update_ntp", "add_snmp_community", "firmware_upgrade", "add_vpn_tunnel"}
    request = ChangeRequest("CHG-21", "Template", "Detailed", "alice")
    library.apply("add_vlan", request, {"vlan_id": "20", "vlan_name": "users", "device_id": "edge-1"})
    assert request.implementation_plan.prerequisites
    assert request.risk_assessment.risk_level == "low"
