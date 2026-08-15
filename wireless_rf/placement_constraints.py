"""AP placement constraints."""
class PlacementConstraints:
    """Check placement inputs without inventing dimensions or heights."""
    def check(self,floor_dimensions_m2:float|None,mounting_height_m:float|None)->dict[str,object]:
        """Return feasible or pending survey."""
        missing=[k for k,v in (("floor_dimensions_m2",floor_dimensions_m2),("mounting_height_m",mounting_height_m)) if v is None]
        return {"status":"pending_survey" if missing else "checkable","missing_inputs":missing}
