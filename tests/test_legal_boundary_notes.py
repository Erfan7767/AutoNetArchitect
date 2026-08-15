from governance.legal_boundary_notes import LegalBoundaryNote, LegalBoundaryRegistry

def test_legal_boundary_registry_declares_technical_only_limits():
    registry = LegalBoundaryRegistry()
    subjects = {item.subject for item in registry.all()}
    assert "technical_assessment" in subjects and "emergency_change" in subjects

def test_legal_boundary_note_requires_human_action():
    note = LegalBoundaryNote(note_id="x", subject="custom", statement_en="statement", statement_ar="بيان", limitation="limitation", required_human_action="human action")
    assert note.not_legal_advice is True
