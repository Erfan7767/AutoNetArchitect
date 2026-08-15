"""Wireless RF test."""
from wireless_rf.channel_planner import ChannelPlanner
def test_regional_channels():
    assert ChannelPlanner().plan("ETSI","2.4GHz",3)["channels"] == [1,6,11]
