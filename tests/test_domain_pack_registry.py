from domain_packs.domain_pack_registry import DomainPackRegistry

def test_registry_contains_supported_packs():
    ids = {record.pack_id for record in DomainPackRegistry().list_records()}
    assert {"enterprise_corporate", "banking", "hospital_clinical", "university_campus"}.issubset(ids)
