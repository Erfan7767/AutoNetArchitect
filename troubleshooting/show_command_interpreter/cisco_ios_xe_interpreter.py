"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class CiscoIOSXEInterpreter(VendorShowInterpreter):
    """Interpret common cisco ios_xe read-only outputs."""

    vendor = "cisco"
    platform = "ios_xe"
