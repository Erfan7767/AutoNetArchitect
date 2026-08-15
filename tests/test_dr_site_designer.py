from designers.dr_bc.dr_site_designer import DRSiteDesigner
def test_site_mandatory(): assert DRSiteDesigner().design({})['status']=='blocked_missing_human_data'
