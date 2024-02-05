import pyproj
import shapely.ops
from osgeo import ogr, osr
from shapely import speedups
from shapely.ops import substring

from geometry import PointGeometry, LineGeometry

speedups.disable()
pyproj.network.set_network_enabled(True)
ogr.UseExceptions()


def position_along_line(measure: float, line_geom: ogr.Geometry) -> PointGeometry:
    dist = line_geom.Length() * measure
    return_point = line_geom.Value(dist)
    return_point_geometry = PointGeometry(coordinates=return_point.GetPoints())
    return return_point_geometry


def segment_along_line(start_measure: float, end_measure: float, line_geom: shapely.LineString,
                       spatial_reference: osr.SpatialReference) -> LineGeometry:
    start_distance = line_geom.length * start_measure
    end_distance = line_geom.length * end_measure
    shapely_segment = substring(line_geom, start_dist=start_distance, end_dist=end_distance)
    segment_coordinates = list(shapely_segment.coords)
    line_geometry_segment = get_line_from_point_list(segment_coordinates, spatial_reference)
    return line_geometry_segment


def get_line_from_point_list(point_list: list, spatial_reference: osr.SpatialReference) -> LineGeometry:
    line_geometry = LineGeometry()
    line = ogr.Geometry(ogr.wkbLineString)
    for point in point_list:
        line.AddPoint_2D(point[0], point[1])
    line.AssignSpatialReference(spatial_reference)
    line_geometry.geometry = line
    return line_geometry


def to_shapely(geometry_object: ogr.Geometry, geom_type: str) -> shapely.geometry.base.BaseGeometry:
    shapely_geometry = None
    if geom_type == "point":
        shapely_geometry = shapely.geometry.Point(geometry_object.GetX(), geometry_object.GetY())
    elif geom_type == "polyline":
        shapely_geometry = shapely.geometry.LineString(geometry_object.GetPoints())
    elif geom_type == "polygon":
        shapely_geometry = shapely.geometry.Polygon(geometry_object.GetGeometryRef(0).GetPoints())
    else:
        print("Geometry type not recognized, unable to generate shapely object")
    return shapely_geometry


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


def srs_from_epsg(epsg_code: int) -> osr.SpatialReference:
    if not isinstance(epsg_code, int):
        epsg_code = int(epsg_code)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg_code)
    if srs.Validate() == ogr.OGRERR_CORRUPT_DATA:
        raise ValueError("Invalid EPSG code used to create ogr.SpatialReference")
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


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


def get_polygon(coordinates: list, spatial_reference: osr.SpatialReference) -> ogr.Geometry:
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for coord in coordinates:
        ring.AddPoint_2D(*coord)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    polygon.CloseRings()
    polygon.AssignSpatialReference(spatial_reference)
    return polygon
