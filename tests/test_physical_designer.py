from designers.physical.physical_designer import PhysicalDesigner
def test_physical_pending_without_dimensions(): assert PhysicalDesigner().design({})["status"]=="pending_site_data"
