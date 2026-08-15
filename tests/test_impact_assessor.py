from incident_response.impact_assessor import ImpactAssessor


def test_impact_assessor_uses_explicit_dependencies():
    result = ImpactAssessor().assess(affected_devices=["r1"], affected_services=["dns"], affected_sites=["s1"], affected_users=50, dependency_map={"dns":["auth"]}, topology_links={"r1":["r2"]}, business_impact={"operational_impact":"degraded"})
    assert result.blast_radius in {"localized", "multi_component", "multi_site_or_broad"}
    assert "auth" in result.dependencies_considered


def test_impact_assessor_does_not_fabricate_user_count():
    result = ImpactAssessor().assess(affected_devices=["r1"])
    assert result.affected_users_estimate is None
    assert result.assumptions
