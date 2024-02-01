import json

from base_geometry import BaseGeometry
from utils.geometry_utils import get_point


class PointGeometry(BaseGeometry):
    geometry_type = "point"
    type = "point"

    def __init__(self, geom_json=None, coordinates=None, spatial_reference=None):
        BaseGeometry.__init__(self, geom_json, coordinates, spatial_reference)
        # if one coordinate is passed
        if coordinates and len(coordinates) == 1:
            self.geometry = get_point(coordinates=self.coordinates[0], spatial_reference=spatial_reference)
        # empty geometry
        if coordinates is None and geom_json is None:
            self.geometry = None
        # create geometry using json
        if coordinates is None and geom_json is not None:
            self.geometry = get_point(geom_json=geom_json, spatial_reference=spatial_reference)

    @property
    def X(self):
        return self.geometry.GetX()

    @property
    def Y(self):
        return self.geometry.GetY()

    @property
    def Z(self):
        return self.geometry.GetZ()

    @property
    def JSON(self):
        """
        Create point ESRI JSON dictionary format.  Over-rides BaseGeometry JSON property
        """
        ogr_dict = {"x": self.X, "y": self.Y,
                    "spatialReference": {"wkid": self.spatial_reference.GetAuthorityCode(None)}}
        return json.dumps(ogr_dict)
