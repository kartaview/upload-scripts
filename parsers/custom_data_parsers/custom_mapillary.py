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
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            mapillary_timestamp = description.get("MAPCaptureTime", None)  # 2021_07_24_14_24_04_000
            if mapillary_timestamp is not None:
                # mapillary timestamp exists
                return datetime_from_string(mapillary_timestamp, "%Y_%m_%d_%H_%M_%S_%f")
        return None

    @classmethod
    def _gps_latitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            # mapillary latitude exists return it or None
            latitude = description.get("MAPLatitude", None)
            return latitude
        return None

    @classmethod
    def _gps_longitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            # mapillary longitude exists return it or None
            latitude = description.get("MAPLongitude", None)
            return latitude
        return None

    @classmethod
    def _gps_compass(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            # mapillary compass exists return it or None
            compass_dict = description.get("MAPCompassHeading", {})
            compass = compass_dict.get("TrueHeading", None)
            return compass
        return None

    @classmethod
    def _gps_altitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            # mapillary altitude exists return it or None
            altitude = description.get("MAPAltitude", None)
            return altitude
        return None

    @classmethod
    def _gps_speed(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            # mapillary speed exists return it or None
            speed = description.get("MAPGPSSpeed", None)
            return speed
        return None

    @classmethod
    def _device_model(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            # mapillary device model exists return it or None
            speed = description.get("MAPDeviceModel", None)
            return speed
        return None

    @classmethod
    def _device_make(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        if ExifTags.DESCRIPTION.value in gps_data:
            description = str(gps_data[ExifTags.DESCRIPTION.value])
            try:
                description = json.loads(description)
            except json.JSONDecodeError as _:
                return None
            # mapillary device make exists return it or None
            make = description.get("MAPDeviceMake", None)
            return make
        return None

    def _device_item(self, tags_data=None) -> OSCDevice:
        device = super()._device_item(tags_data)
        if device.platform_name is None or "iPhone" in device.platform_name:
            if "iPhone" in device.device_raw_name:
                device.platform_name = "Apple"
            else:
                device.platform_name = "Unknown"

        return device
