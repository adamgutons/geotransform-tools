import pyproj
from osgeo import ogr, osr
from pyproj.transformer import TransformerGroup
from shapely.ops import transform as shapely_transform

from geometry import BaseGeometry, LineGeometry, PointGeometry, PolygonGeometry
from geometry_driver import srs_from_epsg, get_polygon


class CoordinateTransformation:
    def __init__(self, logger, spatial_reference=None, intermediate_reference=None,
                 transform_type="REPROJECT", transform_idx=0, proj_string=False, **kwargs):
        """
        A class for handling coordinate transformations.  Fundamentally the pyproj and GDAL libraries are powering any
        mathematical forumlas.  This class acts as a container for configurable coordinate transformation and
        re-projection options found in config.json -> outputs -> parameters -> coordinate_transformation
        @param logger: LoggingService
        @param spatial_reference: str/int, EPSG code value for the final spatial reference
        @param intermediate_reference: str/int, EPSG code value for spatial reference to convert to before the final
        @param transform_type: str, the type of overall transformation steps to perform
        @param transform_idx: int, a value used to specify a particular transformation in def create_transformation
        @param kwargs: catches any unnecessary config.json parameters
        """
        self.logger = logger
        self.transform_type = transform_type
        self.spatial_reference_epsg = spatial_reference
        self.intermediate_reference_epsg = intermediate_reference
        self.proj_string = proj_string
        if spatial_reference:
            self.spatial_reference = srs_from_epsg(spatial_reference)
        if transform_type == "REPROJECT_WITH_TRANSFORM":
            self.transformer = self.create_transformation(intermediate_reference, spatial_reference, logger,
                                                          transform_idx)
        if intermediate_reference:
            self.intermediate_reference = srs_from_epsg(intermediate_reference)
            self.transformer = self.create_transformation(intermediate_reference, spatial_reference, logger,
                                                          transform_idx)
        if proj_string:
            self.transform_type = "PROJ_STRING"
            self.transformer = self.create_transformation_from_proj_string(proj_string)

    def transform(self, record):
        """
        This function delegates projection/transformation steps based on config.json transformation type string
        @param record: Entity
        """
        if self.transform_type == "REPROJECT":
            self.reproject(record)
        elif self.transform_type in ("REPROJECT_WITH_TRANSFORM", "PROJ_STRING"):
            self.reproject_with_transform(record)
        elif self.transform_type == "REPROJECT_WITH_INTERMEDIATE":
            self.reproject_with_intermediate_reference(record)

    def reproject(self, geometry: BaseGeometry) -> None:
        """
        When transform_type = REPROJECT this function simply calls on the GDAL Geometry TransformTo function that will
        perform a simple reprojection to the final spatial_reference
        @param geometry: point, line or polygon
        """
        # simple coordinate re-projection, no named transformation
        geometry.geometry.TransformTo(self.spatial_reference)

    def reproject_with_transform(self, geometry):
        """
        When transform_type = REPROJECT_WITH_TRANSFORM self.transformation is created upon instantiation.
        self.transformation is a pyproj Transformer object that applies a named transformation to the coordinate
        re-projection.
        @param geometry: point, line or polygon
        """
        self.transform_geometry(geometry=geometry,
                                transformer=self.transformer,
                                osr_reference=self.spatial_reference)

    def reproject_with_intermediate_reference(self, geometry):
        """
        When an intermediate_reference parameter is supplied self.transformation is created upon instantiation.
        This function calls on the GDAL Geometry TransformTo function before delegating a named transformation to the
        coordinate re-projection in self.transform_geometry
        @param geometry: point, line or polygon
        """
        geometry.geometry.TransformTo(self.intermediate_reference)
        self.transform_geometry(geometry=geometry,
                                transformer=self.transformer,
                                osr_reference=self.spatial_reference)

    @classmethod
    def create_transformation(cls, from_epsg: str, transform_epsg: str, logger: "Logger", idx=0):
        """
        This function uses the pyproj library to create a list of available transformation options between two EPSG
        codes
        @param from_epsg: str, the EPSG of the starting spatial reference.
        @param transform_epsg: str, the EPSG of the spatial reference to transform to
        @param logger: LoggingService
        @param idx: int, by default idx=0 is used to select the first available transformation from the list
        """
        transformations = TransformerGroup(f"epsg:{from_epsg}",
                                           f"epsg:{transform_epsg}", always_xy=True)
        if not transformations.transformers:
            logger.critical("Transformers not available, please check provided epsg codes to TransformerGroup.")
        else:
            try:
                return transformations.transformers[idx]
            except IndexError as e:
                logger.critical(
                    f"Transformation not found in list\nepsg:{from_epsg}, epsg:{transform_epsg}\n\t[+]{transformations.transformers}")

    @classmethod
    def create_transformation_from_proj_string(cls, proj_string):
        try:
            return pyproj.Transformer.from_pipeline(proj_string)
        except Exception:
            cls.logger.error(f"Issue when creating Transformer from pipeline {proj_string}")

    @classmethod
    def transform_geometry(cls, geometry: BaseGeometry, transformer: pyproj.Transformer,
                           osr_reference: osr.SpatialReference):
        """
        This function uses the pyproj.Transformer object to perform coordinate re-projection and transformation.  The
        new coordinate values are then set directly on the geometry object
        @param geometry: BaseGeometry
        @param transformer: pyproj.Transformer, a transformation function to be applied
        @param osr_reference: osr.SpatialReference, the final output spatial reference for the newly created geometry
        """
        if isinstance(geometry, PointGeometry):
            new_point = transformer.transform(geometry.X, geometry.Y)
            new_point_geometry = ogr.Geometry(ogr.wkbPoint)
            new_point_geometry.AssignSpatialReference(osr_reference)
            new_point_geometry.AddPoint_2D(*new_point)
            geometry.geometry = new_point_geometry
        if isinstance(geometry, LineGeometry):
            record_geometry = shapely_transform(transformer.transform, geometry.to_shapely())
            new_line_geometry = ogr.Geometry(ogr.wkbLineString)
            # record_geometry is now a shapely LineString.  iterate the coords attribute to get each point
            for point in record_geometry.coords:
                new_line_geometry.AddPoint_2D(*point)
            new_line_geometry.AssignSpatialReference(osr_reference)
            geometry.geometry = new_line_geometry
        if isinstance(geometry, PolygonGeometry):
            record_geometry = shapely_transform(transformer.transform, geometry.to_shapely())
            new_polygon_geometry = get_polygon(record_geometry.exterior.coords, osr_reference)
            geometry.geometry = new_polygon_geometry
