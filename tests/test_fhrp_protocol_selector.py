from designers.fhrp.fhrp_protocol_selector import FHRPProtocolSelector
def test_multivendor_vrrp(): assert FHRPProtocolSelector().design({"multi_vendor":True})["protocol"]=="vrrp"
