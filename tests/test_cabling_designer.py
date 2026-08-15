from designers.physical.cabling_designer import CablingDesigner
def test_cabling_import(): assert CablingDesigner().design({})["distance_validation"]=="pending_site_measurement"
