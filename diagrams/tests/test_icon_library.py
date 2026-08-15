from diagrams.icon_library import IconLibrary

def test_icon_library_uses_vendor_and_generic_fallback():
    library = IconLibrary()
    assert library.select(vendor="cisco", node_type="router").startswith("cisco/")
    assert library.select(vendor="unknown-vendor", node_type="router").startswith("generic/")
