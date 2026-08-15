from designers.access_control.radius_infrastructure_designer import RadiusInfrastructureDesigner
def test_radius_mandatory(): assert RadiusInfrastructureDesigner().design({})["status"]=="blocked_missing_human_data"
