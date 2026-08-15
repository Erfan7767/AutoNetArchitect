from domain_packs.banking.secure_segmentation import BankingSecureSegmentation

def test_banking_segments_include_sensitive_zones():
    result = BankingSecureSegmentation().design({"sector": "banking"})
    assert {"payment_processing", "atm", "management", "guest"}.issubset(set(result["artifact"]["zones"]))
