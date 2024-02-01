import pyproj
import shapely.ops
from osgeo import ogr, osr
from shapely import speedups
from shapely.ops import substring

from geometry import PointGeometry, LineGeometry

speedups.disable()
pyproj.network.set_network_enabled(True)
ogr.UseExceptions()


def position_along_line(measure, line_geom):
    """
    Create a point at a position along the input line based on a measure percentage value.  Values should be in the
    range of 0.0 to 1.0
    Args:
        measure: float
        line_geom: ogr Geometry object (pass in from LineGeometry self instance)

    Returns: PointGeometry

    """
    dist = line_geom.Length() * measure
    return_point = line_geom.Value(dist)
    return_point_geometry = PointGeometry(coordinates=return_point.GetPoints())
    return return_point_geometry


def segment_along_line(start_measure: float, end_measure: float, line_geom: shapely.LineString,
                       spatial_reference: osr.SpatialReference) -> LineGeometry:
    """
    Create a segment along the input line based on start/end percentage values 0-100% (values should be in the
    range of 0.0 to 1.0).
    Args:
        start_measure: float
        end_measure: float
        line_geom: shapely LineString class
        spatial_reference: osr.SpatialReference
    Returns: LineGeometry object
    """
    start_distance = line_geom.length * start_measure
    end_distance = line_geom.length * end_measure
    shapely_segment = substring(line_geom, start_dist=start_distance, end_dist=end_distance)
    segment_coordinates = list(shapely_segment.coords)
    line_geometry_segment = get_line_from_point_list(segment_coordinates, spatial_reference)
    return line_geometry_segment


def get_line_from_point_list(point_list: list, spatial_reference: osr.SpatialReference) -> LineGeometry:
    """
    Create a LineGeometry from a list of point coordinates
    Args:
        point_list: container of coordinate pairs i.e. list of lists
        spatial_reference: osr.SpatialReference
    Returns:
        line_geometry: LineGeometry object
    """
    line_geometry = LineGeometry()
    line = ogr.Geometry(ogr.wkbLineString)
    for point in point_list:
        line.AddPoint_2D(point[0], point[1])
    line.AssignSpatialReference(spatial_reference)
    line_geometry.geometry = line
    return line_geometry


def feet_to_meters(feet):
    """
    See https://geodesy.noaa.gov/faq.shtml#Feet
    Converts feet to meters
    Args:
        feet: int

    Returns: feet converted to meters

    """
    return float(feet) / 3.280833333


def to_shapely(geometry_object, geom_type):
    """
    Convert ogr geometry to shapely geometry class
    Returns: shapely Point, LineString,

    """
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


def get_coordinates(geom_json):
    """
    Parses the geom_json coordinates and attaches them as an attribute to BaseGeometry
    Args:
        geom_json: a single dict or list of geometry dicts returned from the api, a list of geometry dicts
                    indicates an api string
    Returns: coordinates, a list of lists, each list containing a coordinate pair

    """
    if geom_json is None:
        return
    coordinates = []
    # if api line
    if isinstance(geom_json, list):
        for point in geom_json:
            longitude = point['longitude']
            latitude = point['latitude']
            coordinates.append([longitude, latitude])
    # if api point
    else:
        longitude = geom_json['longitude']
        latitude = geom_json['latitude']
        coordinates.append([longitude, latitude])
    return coordinates


def srs_from_epsg(epsg_code: int) -> osr.SpatialReference:
    """
    Create a spatial reference system from a valid EPSG code.  Raises an error if an invalid EPSG is used
    Args:
        epsg_code: int

    Returns: osr.SpatialReference object

    """
    if not isinstance(epsg_code, int):
        epsg_code = int(epsg_code)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg_code)
    if srs.Validate() == ogr.OGRERR_CORRUPT_DATA:
        raise ValueError("Invalid EPSG code used to create ogr.SpatialReference")
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def get_point(geom_json: dict, coordinates: list, spatial_reference: osr.SpatialReference) -> ogr.Geometry:
    """
    Creates a wkbPoint ogr.Geometry object

    Args:
        geom_json: dictionary, the geometry section of the api_json response
        coordinates: list, lon lat coordinate pair, ie [-82.3775, 35.0806]
        spatial_reference: ogr.SpatialReference, currently unused.  Plans to allow custom SR assignment to the
                         PointGeometry geometry

    Returns: return_point, ogr.Geometry point object

    """
    if geom_json and coordinates:
        raise ValueError("Point can not be created from json and input coordinates")
    if geom_json and not coordinates:
        return_point = ogr.Geometry(ogr.wkbPoint)
        return_point.AssignSpatialReference(spatial_reference)
        return_point.AddPoint_2D(geom_json["longitude"], geom_json["latitude"])
        return return_point
    if coordinates and not geom_json:
        # create a point in default spatial reference
        return_point = ogr.Geometry(ogr.wkbPoint)
        return_point.AssignSpatialReference(spatial_reference)
        return_point.AddPoint_2D(coordinates[0], coordinates[1])
        return return_point


def get_line(geom_json: dict, spatial_reference: osr.SpatialReference) -> ogr.Geometry:
    """
    Create an ogr.Geometry line object from API json dictionary
    Args:
        geom_json: list of geometry dicts returned from the api
        spatial_reference: ogr.SpatialReference, currently unused.  Plans to allow custom SR assignment to the
            PointGeometry geometry
    Returns: ogr.LineString geometry

    """
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


def get_polygon(coordinates, spatial_reference):
    """
    Create an ogr.Geometry wkbPolygon object
    Args:
        coordinates: an iterable containing iterables of coordinate pair (long/lat) values
        spatial_reference: osr.SpatialReference object
    Returns:
        polygon = ogr.Geometry ogr.wkbLinearRing
    """
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for coord in coordinates:
        ring.AddPoint_2D(*coord)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    polygon.CloseRings()
    polygon.AssignSpatialReference(spatial_reference)
    return polygon
