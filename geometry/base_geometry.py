import json

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
    def spatial_reference(self):
        if self.geometry:
            return self.geometry.GetSpatialReference()

    @property
    def points(self):
        if self.geometry:
            return self.geometry.GetPoints()

    @property
    def pointCount(self):
        if self.geometry:
            return self.geometry.GetPointCount()

    @property
    def JSON(self):
        """
        Create ESRI geometry JSON.  The BaseGeometry property is inherited for LineGeometry, MultiLineGeometry, and
        PolygonGeometry classes.  See PointGeometry JSON property for its over-ridden version
        """
        if self.geometry:
            ogr_json = json.loads(self.geometry.ExportToJson())
            json_dict = {
                "paths": [ogr_json["coordinates"]],
                "spatialReference": {"wkid": self.spatial_reference.GetAuthorityCode(None)}
            }
            return json.dumps(json_dict)

    def to_shapely(self):
        """
        Wrapper for driver.to_shapely, sets a new "shapely" attribute to the class that references the ogr geom.
        converted to shapely class
        Returns: shapely geometry class
        """
        return to_shapely(self.geometry, self.geometry_type)

    def to_esri_json(self):
        return

    @spatial_reference.setter
    def spatial_reference(self, value):
        self._spatial_reference = value
