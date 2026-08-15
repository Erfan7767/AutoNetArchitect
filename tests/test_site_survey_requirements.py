"""Field reality test."""
from field_reality.site_model import SiteModel
from field_reality.site_survey_requirements import SiteSurveyRequirements
def test_survey():
    assert SiteSurveyRequirements().required_for(SiteModel("s", "office"))
