"""
This module contains custom mapillary images parsers.
"""
import json
import os
from typing import Dict, Optional

import exifread
from exifread.classes import IfdTag

from common.models import PhotoMetadata, GPS, Compass, OSCDevice, RecordingType
from parsers.exif.exif import ExifParser
from parsers.exif.utils import ExifTags, datetime_from_string, maker_name, device_model


class MapillaryExif(ExifParser):

    def _all_tags(self) -> Dict[str, IfdTag]:
        """Method to return Exif tags"""
        with self._storage.open(self.file_path, "rb") as file:
            tags = exifread.process_file(file, details=True, truncate_tags=False)
        return tags

    @classmethod
    def _gps_timestamp(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            # description exists
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            mapillary_timestamp = description.get("MAPCaptureTime", None)  # 2021_07_24_14_24_04_000
            if mapillary_timestamp is not None:
                # mapillary timestamp exists
                return datetime_from_string(mapillary_timestamp, "%Y_%m_%d_%H_%M_%S_%f")
            return None

    @classmethod
    def _gps_latitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            # mapillary latitude exists return it or None
            latitude = description.get("MAPLatitude", None)
            return latitude

    @classmethod
    def _gps_longitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            # mapillary longitude exists return it or None
            latitude = description.get("MAPLongitude", None)
            return latitude

    @classmethod
    def _gps_compass(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            # mapillary compass exists return it or None
            compass_dict = description.get("MAPCompassHeading", {})
            compass = compass_dict.get("TrueHeading", None)
            return compass

    @classmethod
    def _gps_altitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            # mapillary altitude exists return it or None
            altitude = description.get("MAPAltitude", None)
            return altitude

    @classmethod
    def _gps_speed(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            # mapillary speed exists return it or None
            speed = description.get("MAPGPSSpeed", None)
            return speed

    @classmethod
    def _device_model(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            # mapillary device model exists return it or None
            speed = description.get("MAPDeviceModel", None)
            return speed

    @classmethod
    def _device_make(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            description = json.loads(description)
            # mapillary device make exists return it or None
            make = description.get("MAPDeviceMake", None)
            return make

    def _gps_item(self, data=None) -> Optional[GPS]:
        if data is not None:
            tags_data = data
        else:
            tags_data = self._all_tags()
        gps = GPS()
        # required gps timestamp or exif timestamp

        gps.timestamp = MapillaryExif._gps_timestamp(tags_data)
        # required latitude and longitude
        gps.latitude = MapillaryExif._gps_latitude(tags_data)
        gps.longitude = MapillaryExif._gps_longitude(tags_data)
        if not gps.latitude or \
                not gps.longitude or \
                not gps.timestamp:
            return None

        # optional data
        gps.speed = self._gps_speed(tags_data)
        gps.altitude = self._gps_altitude(tags_data)
        return gps

    def _compass_item(self, data=None) -> Optional[Compass]:
        if data is not None:
            tags_data = data
        else:
            tags_data = self._all_tags()
        compass = Compass()
        compass.compass = self._gps_compass(tags_data)

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

        file_name = os.path.basename(self.file_path)
        if file_name.isdigit():
            photo.frame_index = int(file_name)

        photo.timestamp = photo.gps.timestamp
        return photo

    def _device_item(self, tags_data=None) -> OSCDevice:
        if tags_data is None:
            tags_data = self._all_tags()

        device = OSCDevice()
        device.timestamp = self._gps_timestamp(tags_data)
        device.device_raw_name = self._device_model(tags_data)
        device_make = self._device_make(tags_data)
        if device_make is None or "iPhone" in device_make:
            if "iPhone" in device.device_raw_name:
                device_make = "Apple"
            else:
                device_make = "Unknown"
        device.platform_name = device_make
        device.recording_type = RecordingType.PHOTO

        return device
