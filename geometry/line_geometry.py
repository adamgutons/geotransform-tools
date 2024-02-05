from osgeo import ogr

from base_geometry import BaseGeometry
from point_geometry import PointGeometry
from utils.geometry_utils import get_line, position_along_line, segment_along_line


class LineGeometry(BaseGeometry):
    geometry_type = "polyline"
    type = "polyline"
    _lineType = None
    _points = None
    _pointCount = None
    _firstPoint = None
    _lastPoint = None
    _length = None

    def __init__(self, geom_json=None, coordinates=None, ogr_json=None, ogr_wkb=None, spatial_reference=None):
        BaseGeometry.__init__(self, geom_json, coordinates, spatial_reference)
        if coordinates is None and geom_json is None:
            self.geometry = None
        elif ogr_wkb:
            self.geometry = ogr.CreateGeometryFromWkb(ogr_wkb)
            self.geometry.AssignSpatialReference(spatial_reference)
            self.geometry.FlattenTo2D()
        elif ogr_json:
            self.geometry = ogr.CreateGeometryFromJson(ogr_json)
            self.geometry.AssignSpatialReference(spatial_reference)
            self.geometry.FlattenTo2D()
            # geom_json attribute becomes the json string used to construct the geometry
            self.geom_json = ogr_json
        else:
            self.geometry = get_line(geom_json, spatial_reference)

    @property
    def lineType(self) -> str:
        if self.geometry:
            self._lineType = self.geometry.GetGeometryName()
        else:
            self._lineType = None
        return self._lineType

    @property
    def firstPoint(self) -> float:
        return self.points[0]

    @property
    def lastPoint(self) -> float:
        return self.points[-1]

    @property
    def length(self) -> float:
        if self.geometry:
            return self.geometry.Length()

    @property
    def partCount(self) -> int:
        if self.geometry:
            return self.geometry.GetGeometryCount()

    def segment_along_line(self, start_measure, end_measure) -> "LineGeometry":
        return segment_along_line(start_measure, end_measure, self.to_shapely(), self.spatial_reference)

    def position_along_line(self, measure) -> PointGeometry:
        return position_along_line(measure, self.geometry)
