"""Regional band and spectrum constraints."""
class SpectrumConstraints:
    """Validate bands against region-specific catalog entries."""
    BANDS={"ETSI":{"2.4GHz":[1,6,11],"5GHz":[36,40,44,48]},"FCC":{"2.4GHz":[1,6,11],"5GHz":[36,40,44,48,149,153,157,161]}}
    def channels(self,region:str,band:str)->list[int]:
        """Return allowed channels or reject unknown region/band."""
        return self.BANDS.get(region,{}).get(band,[])
