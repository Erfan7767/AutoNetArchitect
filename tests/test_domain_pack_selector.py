from domain_packs.domain_pack_selector import DomainPackSelector

def test_explicit_sector_selection_is_traceable():
    result = DomainPackSelector().select({"sector": "banking"})
    assert result["selected_pack"] == "banking"
    assert result["inference"]["confidence"] == 1.0
