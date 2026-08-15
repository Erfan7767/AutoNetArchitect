"""Core designer test."""
from designers.wireless.wireless_designer import WirelessDesigner
def test_wireless_not_rf(): assert WirelessDesigner().design({})["rf_status"]=="not_validated"
