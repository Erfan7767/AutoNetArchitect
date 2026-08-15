"""Scope control test."""
from scope_control.scale_boundaries import ScaleBoundaries
def test_scale():
    assert not ScaleBoundaries().allowed(501)
