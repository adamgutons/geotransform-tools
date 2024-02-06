import json

from osgeo import ogr, osr

from geometry.base_geometry import BaseGeometry


def get_point(geom_json: dict, coordinates: list, spatial_reference: osr.SpatialReference) -> ogr.Geometry:
    if geom_json and coordinates:
        raise ValueError("Point can not be created from json and input coordinates")
    if geom_json and not coordinates:
        return_point = ogr.Geometry(ogr.wkbPoint)
        return_point.AssignSpatialReference(spatial_reference)
        return_point.AddPoint_2D(geom_json["longitude"], geom_json["latitude"])
        return return_point
    if coordinates and not geom_json:
        return_point = ogr.Geometry(ogr.wkbPoint)
        return_point.AssignSpatialReference(spatial_reference)
        return_point.AddPoint_2D(coordinates[0], coordinates[1])
        return return_point


class PointGeometry(BaseGeometry):
    geometry_type = "point"
    type = "point"

    def __init__(self, geom_json=None, coordinates=None, spatial_reference=None):
        BaseGeometry.__init__(self, geom_json, coordinates, spatial_reference)
        # if one coordinate is passed
        if coordinates and len(coordinates) == 1:
            self.geometry = get_point(geom_json=geom_json, coordinates=self.coordinates[0],
                                      spatial_reference=spatial_reference)
        # empty geometry
        if coordinates is None and geom_json is None:
            self.geometry = None
        # create geometry using json
        if coordinates is None and geom_json is not None:
            self.geometry = get_point(geom_json=geom_json, spatial_reference=spatial_reference)

    @property
    def X(self) -> float:
        return self.geometry.GetX()

    @property
    def Y(self) -> float:
        return self.geometry.GetY()

    @property
    def Z(self) -> float:
        return self.geometry.GetZ()

    @property
    def JSON(self) -> str:
        """
        Create point ESRI JSON
        """
        ogr_dict = {"x": self.X, "y": self.Y,
                    "spatialReference": {"wkid": self.spatial_reference.GetAuthorityCode(None)}}
        return json.dumps(ogr_dict)
