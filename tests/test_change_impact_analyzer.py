from datetime import timedelta

from change_management import ChangeImpactAnalyzer, ChangeRequest, DeviceRef, ServiceRef, SiteRef


def test_change_impact_analyzer_expands_explicit_dependencies_and_classifies_impact():
    request = ChangeRequest("CHG-4", "Route change", "Detailed", "alice", affected_devices=[DeviceRef("edge-1", site_id="site-1")], affected_services=[ServiceRef("dns")], affected_sites=[SiteRef("site-1")])
    result = ChangeImpactAnalyzer().analyze(request, dependency_map={"edge-1": ["core-1"]}, service_dependency_map={"dns": ["aaa"]}, expected_downtime=timedelta(minutes=5), user_counts={"edge-1": 100, "site-1": 100})
    assert result.direct_device_ids == ("edge-1",)
    assert result.indirect_device_ids == ("core-1",)
    assert set(result.affected_service_ids) == {"aaa", "dns"}
    assert result.impact_class == "moderate_impact"
    assert result.affected_user_count == 200
