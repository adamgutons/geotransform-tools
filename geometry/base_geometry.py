import json

import shapely
from osgeo import osr

from geometry_transformer import GeometryTransformer


def get_coordinates(geom_json: dict) -> list:
    coordinates = []
    if geom_json is None:
        return coordinates
    if isinstance(geom_json, list):
        for point in geom_json:
            longitude = point['longitude']
            latitude = point['latitude']
            coordinates.append([longitude, latitude])
    else:
        longitude = geom_json['longitude']
        latitude = geom_json['latitude']
        coordinates.append([longitude, latitude])
    return coordinates


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
        shapely_geometry = None
        if self.geometry_type == "point":
            shapely_geometry = shapely.geometry.Point(self.geometry.GetX(), self.geometry.GetY())
        elif self.geometry_type == "polyline":
            shapely_geometry = shapely.geometry.LineString(self.geometry.GetPoints())
        elif self.geometry_type == "polygon":
            shapely_geometry = shapely.geometry.Polygon(self.geometry.GetGeometryRef(0).GetPoints())
        else:
            print("Geometry type not recognized, unable to generate shapely object")
        return shapely_geometry

    def transform_to(self, epsg: int, proj_str: str = None) -> None:
        geometry_transformer = GeometryTransformer(epsg, proj_str)
        geometry_transformer.transform(self)

    @spatial_reference.setter
    def spatial_reference(self, value):
        self._spatial_reference = value
