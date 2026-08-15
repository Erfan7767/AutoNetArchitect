from designers.interface.interface_inventory_builder import InterfaceInventoryBuilder
def test_missing_map_is_mandatory(): assert InterfaceInventoryBuilder().design({})["status"]=="HumanSuppliedMandatory"
