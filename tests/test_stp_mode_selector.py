from designers.l2_protocols.stp.stp_mode_selector import STPModeSelector
def test_scale_selects_mstp():
    assert STPModeSelector().design({"vlan_count":200})["mode"]=="mstp"
