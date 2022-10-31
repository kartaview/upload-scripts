"""
This module contains custom mapillary images parsers.
"""
import json
from typing import Dict, Optional

from exifread.classes import IfdTag

from common.models import OSCDevice
from parsers.exif.exif import ExifParser
from parsers.exif.utils import ExifTags, datetime_from_string


class MapillaryExif(ExifParser):

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

    def _device_item(self, tags_data=None) -> OSCDevice:
        device = super(MapillaryExif, self)._device_item()
        if device.platform_name is None or "iPhone" in device.platform_name:
            if "iPhone" in device.device_raw_name:
                device_make = "Apple"
            else:
                device_make = "Unknown"
        device.platform_name = device_make

        return device
