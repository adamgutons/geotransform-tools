from osgeo import ogr, osr
from shapely.ops import substring

from geometry.base_geometry import BaseGeometry
from geometry.point_geometry import PointGeometry, get_point


def _get_line_from_point_list(point_list: list, spatial_reference: osr.SpatialReference) -> "LineGeometry":
    line_geometry = LineGeometry()
    line = ogr.Geometry(ogr.wkbLineString)
    for point in point_list:
        line.AddPoint_2D(point[0], point[1])
    line.AssignSpatialReference(spatial_reference)
    line_geometry.geometry = line
    return line_geometry


def get_line(geom_json: dict, spatial_reference: osr.SpatialReference) -> ogr.Geometry:
    if geom_json is None:
        pass
    else:
        line = ogr.Geometry(ogr.wkbLineString)
        for point in geom_json:
            pnt = get_point(point, coordinates=[], spatial_reference=spatial_reference)
            longitude = pnt.GetX()
            latitude = pnt.GetY()
            line.AddPoint_2D(longitude, latitude)
        line.AssignSpatialReference(spatial_reference)
        return line


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
        start_distance = self.length * start_measure
        end_distance = self.length * end_measure
        shapely_segment = substring(self.to_shapely(), start_dist=start_distance, end_dist=end_distance)
        segment_coordinates = list(shapely_segment.coords)
        line_geometry_segment = _get_line_from_point_list(segment_coordinates, self.geometry.GetSpatialReference())
        return line_geometry_segment

    def position_along_line(self, measure) -> PointGeometry:
        dist = self.geometry.Length() * measure
        return_point = self.geometry.Value(dist)
        return_point_geometry = PointGeometry(coordinates=return_point.GetPoints())
        return return_point_geometry
