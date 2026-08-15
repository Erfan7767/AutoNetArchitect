from domain_packs.enterprise_corporate.domain_scope import EnterpriseCorporatePack

def test_domain_is_opt_in_and_exclusive():
    pack = EnterpriseCorporatePack()
    assert pack.design({"sector": "enterprise_corporate"})["scope_guard"]["applicable"] is True
    assert pack.design({"sector": "healthcare"})["scope_guard"]["status"] == "out_of_scope"
