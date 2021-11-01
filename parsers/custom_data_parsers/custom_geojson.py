from typing import Type, List, Optional
from geojson import load
from io_storage.storage import Storage
from parsers.base import BaseParser
from parsers.geojson import GeoJsonParser
from common.models import GPS, Compass, SensorItem
from parsers.custom_data_parsers.custom_models import PhotoGeoJson
import datetime


class FeaturePhotoGeoJsonParser(GeoJsonParser):

    def __init__(self, file_path, storage):
        super(FeaturePhotoGeoJsonParser, self).__init__(file_path, storage)
        self._sensors: List[PhotoGeoJson] = []
        self._data_pointer: int = 0
        with self._storage.open(self.file_path, 'r') as geo_json_file:
            geo_json = load(geo_json_file)
            for feature in geo_json["features"]:
                photo = PhotoGeoJson()
                photo.frame_index = int(feature.properties['order'])
                photo.gps = GPS()
                string_time = feature.properties['Timestamp']
                utc_time = datetime.datetime.strptime(string_time,
                                                      "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
                photo.gps.timestamp = utc_time.timestamp()
                photo.gps.latitude = float(feature.properties['Lat'])
                photo.gps.longitude = float(feature.properties['Lon'])
                photo.compass = Compass()
                photo.compass.compass = feature.properties['direction']
                photo.relative_image_path = feature.properties['path']
                self._sensors.append(photo)
        self._sensors.sort(key=lambda x: x.frame_index)

    @classmethod
    def valid_parser(cls, file_path: str, storage: Storage) -> BaseParser:
        """this method will return a valid parser"""
        return FeaturePhotoGeoJsonParser(file_path, storage)

    def items(self) -> List[SensorItem]:
        return list(self._sensors)

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        if item_class not in self.compatible_sensors():
            return list()
        if item_class is PhotoGeoJson:
            return list(self._sensors)
        if item_class is GPS:
            return [photo.gps for photo in self._sensors]
        if item_class is Compass:
            return [photo.compass for photo in self._sensors]
        return list()

    def next_item(self) -> Optional[SensorItem]:
        if len(self._sensors) < self._data_pointer + 1:
            self._data_pointer += 1
            return self._sensors[self._data_pointer]
        else:
            return None

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        items = self.items_with_class(item_class)
        if len(items) < self._data_pointer + 1:
            self._data_pointer += 1
            return items[self._data_pointer]
        else:
            return None

    def format_version(self) -> Optional[str]:
        return "unknown"

    def start_new_reading(self):
        self._data_pointer = 0

    def compatible_sensors(self):
        return [PhotoGeoJson, GPS, Compass]
