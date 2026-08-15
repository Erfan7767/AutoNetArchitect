"""Vendor-specific bounded show-command interpreter."""

from .vendor_interpreter import VendorShowInterpreter


class HuaweiInterpreter(VendorShowInterpreter):
    """Interpret common huawei vrp read-only outputs."""

    vendor = "huawei"
    platform = "vrp"
