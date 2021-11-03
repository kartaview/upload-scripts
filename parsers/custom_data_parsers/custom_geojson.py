"""
This module constains custom geosjon parsers.
"""
from typing import Type, List, Optional
import datetime

from geojson import load
from io_storage.storage import Storage
from parsers.geojson import GeoJsonParser
from parsers.custom_data_parsers.custom_models import PhotoGeoJson
from common.models import GPS, Compass, SensorItem


class FeaturePhotoGeoJsonParser(GeoJsonParser):

    def __init__(self, file_path: str, storage: Storage):
        super().__init__(file_path, storage)
        self._sensors: List[PhotoGeoJson] = []
        self._data_pointer: int = 0
        self._version = "unknown"
        with self._storage.open(self.file_path, 'r') as geo_json_file:
            geo_json = load(geo_json_file)
            for feature in geo_json["features"]:
                string_time = feature.properties['Timestamp']
                utc_time = datetime.datetime.strptime(string_time, "%Y-%m-%dT%H:%M:%SZ")
                utc_time = utc_time.replace(tzinfo=datetime.timezone.utc)
                gps = GPS.gps(utc_time.timestamp(),
                              float(feature.properties['Lat']),
                              float(feature.properties['Lon']))
                photo = PhotoGeoJson(gps,
                                     int(feature.properties['order']),
                                     feature.properties['path'].replace("\\", "/"))
                photo.compass = Compass()
                photo.compass.compass = feature.properties['direction']
                self._sensors.append(photo)
            crs_string = geo_json.get('crs', {}).get('properties', {}).get("name", None)
            crs_values = crs_string.split(":")
            if crs_string and len(crs_values) == 7:
                self._version = crs_values[5]

        self._sensors.sort(key=lambda x: x.frame_index)

    def items(self) -> List[SensorItem]:
        return self._sensors

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        if item_class not in self.compatible_sensors():
            return []
        if item_class is PhotoGeoJson:
            return self._sensors
        if item_class is GPS:
            return [photo.gps for photo in self._sensors]
        if item_class is Compass:
            return [photo.compass for photo in self._sensors]
        return []

    def next_item(self) -> Optional[SensorItem]:
        if len(self._sensors) < self._data_pointer + 1:
            self._data_pointer += 1
            return self._sensors[self._data_pointer]

        return None

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        items = self.items_with_class(item_class)
        if len(items) < self._data_pointer + 1:
            self._data_pointer += 1
            return items[self._data_pointer]
        return None

    def format_version(self) -> Optional[str]:
        return self._version

    def start_new_reading(self):
        self._data_pointer = 0

    @classmethod
    def compatible_sensors(cls):
        return [PhotoGeoJson, GPS, Compass]
