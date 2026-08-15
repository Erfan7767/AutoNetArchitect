from types import SimpleNamespace
from review_console.alternative_viewer import AlternativeViewer

def test_alternative_viewer_does_not_recompute_scores():
    rows = AlternativeViewer().build(chosen_name="a", ranked=[SimpleNamespace(alternative_name="a", total_score=5.5, rejection_reasons=[], constraint_results=[])], explanation={"rejected_options": [{"option": "b", "score": 3.0, "rejection_reasons": ["hard constraint"]}]})
    assert rows[0].selected and rows[0].score == 5.5 and rows[1].rejection_reasons == ("hard constraint",)
