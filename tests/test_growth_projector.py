from traffic_analysis.growth_projector import GrowthProjector
from traffic_analysis.models import GrowthModel

def test_growth_projector_marks_default_rate_as_assumption():
    result = GrowthProjector().project(subject_id="l1", current_mbps=100, model=GrowthModel.EXPONENTIAL)
    assert result.projections_mbps["12_months"] > 100
    assert result.assumptions

def test_growth_projector_uses_explicit_rate():
    result = GrowthProjector().project(subject_id="l1", current_mbps=100, model=GrowthModel.LINEAR, annual_growth_rate_percent=10)
    assert result.projections_mbps["12_months"] == 110
