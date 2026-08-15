"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class CiscoNXOSInterpreter(VendorShowInterpreter):
    """Interpret common cisco nxos read-only outputs."""

    vendor = "cisco"
    platform = "nxos"
