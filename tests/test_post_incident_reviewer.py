from incident_response.post_incident_reviewer import PostIncidentReviewer
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity
from datetime import datetime, timezone

def test_post_incident_reviewer_requires_p1_review_and_is_blame_free():
    incident = Incident(incident_id="INC-20260814-0001", title="Issue", description="Issue", severity=IncidentSeverity.P1_CRITICAL, priority=IncidentPriority.CRITICAL, category=IncidentCategory.NETWORK_OUTAGE, detected_at=datetime.now(timezone.utc), detected_by="operator", detection_method=DetectionMethod.ENGINEER)
    review = PostIncidentReviewer().create_review(incident, improvements=["improve detection"])
    assert review.required is True
    assert review.blame_free is True
