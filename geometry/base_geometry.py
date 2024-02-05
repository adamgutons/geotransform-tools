import json

import shapely
from osgeo import osr

from geometry_transformer import GeometryTransformer
from utils.geometry_utils import get_coordinates, to_shapely


class BaseGeometry:
    geometry_type = "point"

    def __init__(self, geom_json=None, coordinates=None, spatial_reference=None):
        self.geometry = None
        self.geom_json = None
        self.spatial_reference = spatial_reference
        if geom_json:
            self.geom_json = geom_json
        if geom_json and coordinates is None:
            self.coordinates = get_coordinates(geom_json)
        else:
            self.coordinates = coordinates

    @property
    def spatial_reference(self) -> osr.SpatialReference:
        if self.geometry:
            return self.geometry.GetSpatialReference()

    @property
    def points(self) -> list:
        if self.geometry:
            return self.geometry.GetPoints()

    @property
    def pointCount(self) -> int:
        if self.geometry:
            return self.geometry.GetPointCount()

    @property
    def JSON(self) -> str:
        """
        Create ESRI geometry JSON
        """
        if self.geometry:
            ogr_json = json.loads(self.geometry.ExportToJson())
            json_dict = {
                "paths": [ogr_json["coordinates"]],
                "spatialReference": {"wkid": self.spatial_reference.GetAuthorityCode(None)}
            }
            return json.dumps(json_dict)

    def to_shapely(self) -> shapely.geometry.base.BaseGeometry:
        return to_shapely(self.geometry, self.geometry_type)

    def to_esri_json(self):
        return

    def transform_to(self, epsg: int, proj_str: str = None) -> None:
        transformer = GeometryTransformer(spatial_reference_epsg=epsg, proj_str=proj_str)
        transformer.transform(self.geometry)

    @spatial_reference.setter
    def spatial_reference(self, value):
        self._spatial_reference = value
