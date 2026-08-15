from review_console.override_panel import OverridePanel

def test_override_panel_displays_provenance_and_revalidation():
    rows = OverridePanel().build(({"override_id": "ov-1", "target_id": "design-1", "target_type": "design_decision", "override_type": "modify_value", "origin": "human_overridden", "status": "applied", "actor_id": "eng", "actor_role": "engineer", "reason": "field constraint", "scope": {"project_id": "p-1"}, "impact": "downstream review", "revalidation_status": "scheduled", "revalidation_trigger_ids": ["reval-1"], "provenance_chain": ["machine-1", "ov-1"]},))
    assert rows[0].origin == "human_overridden" and rows[0].provenance_chain == ("machine-1", "ov-1") and rows[0].revalidation_status == "scheduled"
