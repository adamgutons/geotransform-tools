import json

from base_geometry import BaseGeometry
from utils.geometry_utils import get_polygon


class PolygonGeometry(BaseGeometry):
    geometry_type = "polygon"
    type = "polygon"

    def __init__(self, geom_json=None, coordinates=None, spatial_reference=None):
        BaseGeometry.__init__(self, geom_json, coordinates, spatial_reference)
        if not coordinates and not geom_json:
            self.geometry = None
        if coordinates and not geom_json:
            self.geometry = get_polygon(coordinates=coordinates, spatial_reference=spatial_reference)
            self.geometry.FlattenTo2D()

    @property
    def points(self):
        if self.geometry:
            return self.geometry.GetGeometryRef(0).GetPoints()

    @property
    def JSON(self):
        """
        Create ESRI geometry JSON.
        """
        if self.geometry:
            ogr_json = json.loads(self.geometry.ExportToJson())
            json_dict = {
                "rings": ogr_json["coordinates"],
                "spatialReference": {"wkid": self.spatial_reference.GetAuthorityCode(None)}
            }
            return json.dumps(json_dict)
