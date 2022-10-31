"""Module responsible to parse Exif information from an image"""

import os
from typing import Optional, Dict, List, Type
# third party
import exifread
import imagesize

from exifread.classes import IfdTag

from common.models import (
    PhotoMetadata,
    GPS,
    Compass,
    SensorItem,
    OSCDevice,
    ExifParameters,
    RecordingType)
from parsers.exif.utils import (
    create_required_gps_tags,
    exif_version,
    add_optional_gps_tags,
    add_gps_tags,
    timestamp,
    gps_timestamp,
    gps_longitude,
    gps_latitude,
    gps_speed,
    gps_altitude,
    gps_compass,
    device_model,
    maker_name,
    ExifTags
)
from io_storage.storage import Storage
from parsers.base import BaseParser


class ExifParser(BaseParser):
    """This class is a BaseParser that can parse images having exif"""

    def __init__(self, file_path, storage: Storage):
        super().__init__(file_path, storage)
        self._data_pointer = 0
        self._body_pointer = 0
        self.tags: Dict[str, IfdTag] = self._all_tags()

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        if item_class == PhotoMetadata:
            return self._photo_item(self.tags)
        if item_class == GPS:
            return self._gps_item(self.tags)
        if item_class == Compass:
            return self._compass_item(self.tags)
        if item_class == OSCDevice:
            return self._device_item(self.tags)
        if item_class == ExifParameters:
            return self._exif_item(self.tags)
        return None

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        item = self.next_item_with_class(item_class)
        if item:
            return [item]
        return []

    def next_item(self) -> Optional[SensorItem]:
        if self._data_pointer == 0:
            self._data_pointer = 1
            return self._photo_item(self.tags)
        if self._data_pointer == 1:
            self._data_pointer = 2
            return self._gps_item(self.tags)
        if self._data_pointer == 2:
            self._data_pointer = 3
            return self._compass_item(self.tags)
        if self._data_pointer == 3:
            self._data_pointer = 4
            return self._device_item(self.tags)
        return None

    def items(self) -> List[SensorItem]:
        return [item for item in [self._photo_item(self.tags),
                                  self._gps_item(self.tags),
                                  self._compass_item(self.tags),
                                  self._device_item(self.tags),
                                  self._exif_item(self.tags)] if item]

    def format_version(self):
        return exif_version(self.tags)

    def serialize(self):
        tags = None
        for item in self._sensors:
            gps = None
            compass = None
            if isinstance(item, PhotoMetadata):
                gps, compass = self._gps_compass(item)
            if isinstance(item, GPS):
                gps = item
            if gps:
                tags = create_required_gps_tags(gps.timestamp,
                                                gps.latitude,
                                                gps.longitude)
                add_optional_gps_tags(tags,
                                      gps.speed,
                                      gps.altitude,
                                      None)
            if isinstance(item, Compass):
                add_optional_gps_tags(tags,
                                      None,
                                      None,
                                      compass.compass)
            if tags is not None:
                add_gps_tags(self.file_path, tags)

    @classmethod
    def compatible_sensors(cls):
        return [PhotoMetadata, GPS, Compass, OSCDevice]

    @classmethod
    def _gps_compass(cls, photo_metadata: PhotoMetadata):
        gps = photo_metadata.gps
        compass = photo_metadata.compass
        return gps, compass

    def _all_tags(self) -> Dict[str, IfdTag]:
        """Method to return Exif tags"""
        with self._storage.open(self.file_path, "rb") as file:
            tags = exifread.process_file(file, details=False)
        return tags

    def _gps_item(self, data=None) -> Optional[GPS]:
        if data is not None:
            tags_data = data
        else:
            tags_data = self._all_tags()
        gps = GPS()
        # required gps timestamp or exif timestamp
        gps.timestamp = gps_timestamp(tags_data)
        exif_timestamp = timestamp(tags_data)
        if (not gps.timestamp or
                (exif_timestamp is not None and exif_timestamp > 31556952
                 and abs(gps.timestamp - exif_timestamp) > 31556952)):
            # if there is no gps timestamp or gps timestamp differs with more than 1 year
            # compared to exif_timestamp we choose exif_timestamp
            gps.timestamp = exif_timestamp

        # required latitude and longitude
        gps.latitude = gps_latitude(tags_data)
        gps.longitude = gps_longitude(tags_data)
        if not gps.latitude or \
                not gps.longitude or \
                not gps.timestamp:
            return None

        # optional data
        gps.speed = gps_speed(tags_data)
        gps.altitude = gps_altitude(tags_data)
        return gps

    def _compass_item(self, data=None) -> Optional[Compass]:
        if data is not None:
            tags_data = data
        else:
            tags_data = self._all_tags()
        compass = Compass()
        compass.compass = gps_compass(tags_data)

        if compass.compass:
            return compass
        return None

    def _photo_item(self, tags_data=None) -> Optional[PhotoMetadata]:
        if tags_data is None:
            tags_data = self._all_tags()

        gps = self._gps_item(tags_data)
        if gps is None:
            return None

        compass = self._compass_item(tags_data) or Compass()
        photo = PhotoMetadata()
        photo.gps = gps
        photo.compass = compass
        photo.timestamp = timestamp(tags_data)
        file_name = os.path.basename(self.file_path)
        if file_name.isdigit():
            photo.frame_index = int(file_name)
        if photo.timestamp is None:
            photo.timestamp = photo.gps.timestamp
            return photo
        return photo

    def _device_item(self, tags_data=None) -> OSCDevice:
        if tags_data is None:
            tags_data = self._all_tags()

        device = OSCDevice()
        ori_timestamp = timestamp(tags_data)
        device.timestamp = ori_timestamp if ori_timestamp is not None else gps_timestamp(tags_data)
        device.device_raw_name = device_model(tags_data)
        device.platform_name = maker_name(tags_data)
        device.recording_type = RecordingType.PHOTO

        return device

    def _exif_item(self, tag_data=None) -> Optional[ExifParameters]:
        if tag_data is None:
            tag_data = self._all_tags()
        if ExifTags.WIDTH.value in tag_data and ExifTags.HEIGHT.value in tag_data:
            exif_item = ExifParameters()
            exif_item.width = int(tag_data[ExifTags.WIDTH.value].values[0])
            exif_item.height = int(tag_data[ExifTags.HEIGHT.value].values[0])

            return exif_item
        width, height = imagesize.get(self.file_path)
        if width > 0 and height > 0:
            exif_item = ExifParameters()
            exif_item.width = width
            exif_item.height = height

            return exif_item
        return None
