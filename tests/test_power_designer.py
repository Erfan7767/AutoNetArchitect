from designers.physical.power_designer import PowerDesigner
def test_power_pending(): assert PowerDesigner().design({})["status"]=="pending_site_data"
