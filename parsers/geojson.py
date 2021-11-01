from typing import Optional, List, Type
import time

from geojson import load

from parsers.base import BaseParser
from common.models import SensorItem, GPS

two_way_key = "osctagging"
two_way_value = "twoway"

one_way_key = "osctagging"
one_way_value = "oneway"

closed_key = "osctagging"
closed_value = "closedRoad"

narrow_road_key = "osctagging"
narrow_road_value = "narrowRoad"

other_key = "osctagging"
other_value = "notes"


class GeoJsonParser(BaseParser):
    """this class is a BaseParser that can parse a GPX"""

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        return None

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        return []

    def next_item(self) -> Optional[SensorItem]:
        return None

    def items(self) -> List[SensorItem]:
        with self._storage.open(self.file_path, 'r') as geo_json_file:
            geo_json = load(geo_json_file)
            index = 0
            sensors: List[SensorItem] = []
            for feature in geo_json["features"]:
                geometry = feature["geometry"]
                coordinates = geometry["coordinates"]

                for geometry_coordinate in coordinates:
                    if isinstance(geometry_coordinate, float) and len(coordinates) == 2:
                        # this is a point
                        gps = GPS()
                        gps.timestamp = time.time() + index
                        gps.latitude = coordinates[1]
                        gps.longitude = coordinates[0]
                        sensors.append(gps)
                        break
                    elif isinstance(geometry_coordinate[0], float) and len(geometry_coordinate) == 2:
                        # this is a list of points
                        longitude = geometry_coordinate[0]
                        latitude = geometry_coordinate[1]
                        gps = GPS()
                        gps.timestamp = time.time() + index
                        gps.latitude = latitude
                        gps.longitude = longitude
                        sensors.append(gps)
                        index += 1
                    else:
                        # this is a list of list of points
                        for geometry_point_coordinate in geometry_coordinate[0]:
                            longitude = geometry_point_coordinate[0]
                            latitude = geometry_point_coordinate[1]
                            gps = GPS()
                            gps.timestamp = time.time() + index
                            gps.latitude = latitude
                            gps.longitude = longitude
                            sensors.append(gps)
                            index += 1
        return sensors

    def format_version(self) -> Optional[str]:
        return "unknown"

    def compatible_sensors(self):
        return [GPS]
