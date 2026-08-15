"""Core designer test."""
from designers.redundancy.redundancy_designer import RedundancyDesigner
def test_redundancy(): assert RedundancyDesigner().design({"dual_power":True})["dual_power"]
