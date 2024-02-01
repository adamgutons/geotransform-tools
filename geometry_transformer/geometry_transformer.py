import pyproj
from osgeo import ogr, osr
from shapely.ops import transform as shapely_transform

from geometry import BaseGeometry, LineGeometry, PointGeometry, PolygonGeometry
from utils.geometry_utils import srs_from_epsg, get_polygon

PROJ = "PROJ"
SIMPLE = "SIMPLE"


class GeometryTransformer:
    def __init__(self, spatial_reference_epsg=None, transform_type=SIMPLE, proj_string=False, **kwargs):
        self.transform_type = transform_type
        self.spatial_reference_epsg = spatial_reference_epsg
        self.proj_string = proj_string
        if spatial_reference_epsg:
            self.spatial_reference = srs_from_epsg(spatial_reference_epsg)
        if proj_string:
            self.transform_type = PROJ
            self.transformer = self.create_transformation_from_proj_string(proj_string)

    def transform(self, geometry: BaseGeometry) -> None:
        if self.transform_type == SIMPLE:
            self.reproject(geometry)
        elif self.transform_type == PROJ:
            self.reproject_with_transform(geometry)

    def reproject(self, geometry: BaseGeometry) -> None:
        # simple coordinate re-projection, no named transformation
        geometry.geometry.TransformTo(self.spatial_reference)

    def reproject_with_transform(self, geometry):
        self.transform_geometry(geometry=geometry,
                                transformer=self.transformer,
                                osr_reference=self.spatial_reference)

    @classmethod
    def create_transformation_from_proj_string(cls, proj_string):
        try:
            return pyproj.Transformer.from_pipeline(proj_string)
        except Exception:
            print(f"Issue when using {proj_string}")

    @classmethod
    def transform_geometry(cls, geometry: BaseGeometry, transformer: pyproj.Transformer,
                           osr_reference: osr.SpatialReference):
        if isinstance(geometry, PointGeometry):
            new_point = transformer.transform(geometry.X, geometry.Y)
            new_point_geometry = ogr.Geometry(ogr.wkbPoint)
            new_point_geometry.AssignSpatialReference(osr_reference)
            new_point_geometry.AddPoint_2D(*new_point)
            geometry.geometry = new_point_geometry
        if isinstance(geometry, LineGeometry):
            record_geometry = shapely_transform(transformer.transform, geometry.to_shapely())
            new_line_geometry = ogr.Geometry(ogr.wkbLineString)
            for point in record_geometry.coords:
                new_line_geometry.AddPoint_2D(*point)
            new_line_geometry.AssignSpatialReference(osr_reference)
            geometry.geometry = new_line_geometry
        if isinstance(geometry, PolygonGeometry):
            record_geometry = shapely_transform(transformer.transform, geometry.to_shapely())
            new_polygon_geometry = get_polygon(record_geometry.exterior.coords, osr_reference)
            geometry.geometry = new_polygon_geometry
