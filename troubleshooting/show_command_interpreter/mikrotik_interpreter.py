"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class MikroTikInterpreter(VendorShowInterpreter):
    """Interpret common mikrotik routeros read-only outputs."""

    vendor = "mikrotik"
    platform = "routeros"
