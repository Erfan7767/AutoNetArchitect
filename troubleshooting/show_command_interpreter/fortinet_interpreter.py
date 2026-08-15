"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class FortinetInterpreter(VendorShowInterpreter):
    """Interpret common fortinet fortigate read-only outputs."""

    vendor = "fortinet"
    platform = "fortigate"
