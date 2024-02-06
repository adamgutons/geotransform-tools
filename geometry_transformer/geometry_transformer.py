import pyproj
from osgeo import ogr, osr
from pyproj import Transformer
from shapely.ops import transform as shapely_transform

# from geometry import get_polygon

pyproj.network.set_network_enabled(True)
ogr.UseExceptions()

PROJ = "PROJ"
SIMPLE = "SIMPLE"

def get_polygon(coordinates: list, spatial_reference: osr.SpatialReference) -> ogr.Geometry:
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for coord in coordinates:
        ring.AddPoint_2D(*coord)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    polygon.CloseRings()
    polygon.AssignSpatialReference(spatial_reference)
    return polygon


def srs_from_epsg(epsg_code: int) -> osr.SpatialReference:
    if not isinstance(epsg_code, int):
        epsg_code = int(epsg_code)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg_code)
    if srs.Validate() == ogr.OGRERR_CORRUPT_DATA:
        raise ValueError("Invalid EPSG code used to create ogr.SpatialReference")
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


class GeometryTransformer:
    def __init__(self, spatial_reference_epsg=None, proj_string=False, **kwargs):
        self.spatial_reference_epsg = spatial_reference_epsg
        self.proj_string = proj_string
        self.transform_type = SIMPLE
        if spatial_reference_epsg:
            self.spatial_reference = srs_from_epsg(spatial_reference_epsg)
        if proj_string:
            self.transform_type = PROJ
            self.transformer = self.create_transformation_from_proj_string(proj_string)

    def transform(self, geometry: "BaseGeometry") -> None:
        if self.transform_type == SIMPLE:
            self.reproject(geometry)
        elif self.transform_type == PROJ:
            self.reproject_with_transform(geometry)

    def reproject(self, geometry: "BaseGeometry") -> None:
        geometry.geometry.TransformTo(self.spatial_reference)

    def reproject_with_transform(self, geometry):
        self.transform_geometry(geometry=geometry,
                                transformer=self.transformer,
                                osr_reference=self.spatial_reference)

    @classmethod
    def create_transformation_from_proj_string(cls, proj_string) -> Transformer:
        try:
            return pyproj.Transformer.from_pipeline(proj_string)
        except Exception:
            print(f"Issue when using {proj_string}")

    @classmethod
    def transform_geometry(cls, geometry, transformer: pyproj.Transformer,
                           osr_reference: osr.SpatialReference) -> None:
        if geometry.geometry_type == "point":
            new_point = transformer.transform(geometry.X, geometry.Y)
            new_point_geometry = ogr.Geometry(ogr.wkbPoint)
            new_point_geometry.AssignSpatialReference(osr_reference)
            new_point_geometry.AddPoint_2D(*new_point)
            geometry.geometry = new_point_geometry
        elif geometry.geometry_type == "polyline":
            record_geometry = shapely_transform(transformer.transform, geometry.to_shapely())
            new_line_geometry = ogr.Geometry(ogr.wkbLineString)
            for point in record_geometry.coords:
                new_line_geometry.AddPoint_2D(*point)
            new_line_geometry.AssignSpatialReference(osr_reference)
            geometry.geometry = new_line_geometry
        elif geometry.geometry_type == "polygon":
            record_geometry = shapely_transform(transformer.transform, geometry.to_shapely())
            new_polygon_geometry = get_polygon(record_geometry.exterior.coords, osr_reference)
            geometry.geometry = new_polygon_geometry
