"""Evidence-labelled attenuation library."""
class AttenuationLibrary:
    """Return only explicitly cataloged material values."""
    def __init__(self,materials:dict[str,float]|None=None)->None:self.materials=materials or {}
    def get(self,material:str)->float|None:
        """Return attenuation or None when unknown."""
        return self.materials.get(material)
