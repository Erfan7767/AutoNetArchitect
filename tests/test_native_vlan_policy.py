from designers.l2_protocols.trunk.native_vlan_policy import NativeVLANPolicy
def test_native_vlan_one_invalid():
    assert not NativeVLANPolicy().design({"native_vlan":1})["valid"]
