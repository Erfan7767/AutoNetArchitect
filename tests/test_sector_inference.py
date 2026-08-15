from domain_packs.sector_inference import SectorInference

def test_sector_inference_requires_review_without_explicit_sector():
    result = SectorInference().infer({"sector_signals": {"domain": "medical hospital patient"}})
    assert result["sector"] == "hospital_clinical"
    assert result["review_required"] is True
