from domain_packs.banking.domain_scope import BankingNetworksPack

def test_banking_scope_is_explicit_and_exclusive():
    assert BankingNetworksPack().design({"sector": "banking"})["scope_guard"]["applicable"] is True
    assert BankingNetworksPack().design({"sector": "enterprise_corporate"})["scope_guard"]["status"] == "out_of_scope"
