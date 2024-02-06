from .base_geometry import BaseGeometry
from .point_geometry import PointGeometry
from .line_geometry import LineGeometry
from .polygon_geometry import PolygonGeometry, get_polygon
from shapely import speedups
speedups.disable()
