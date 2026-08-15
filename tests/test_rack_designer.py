from designers.physical.rack_designer import RackDesigner
def test_rack_capacity(): assert RackDesigner().design({"equipment":[{"rack_units":10}],"available_rack_units":5})["status"]=="capacity_exceeded"
