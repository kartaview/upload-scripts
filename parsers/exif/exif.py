"""Module responsible to parse Exif information from an image"""

import os
from typing import Optional, Dict, List, Type
# third party
import exifread
import imagesize

from exifread.classes import Ratio, IfdTag

from common.models import (
    PhotoMetadata,
    GPS,
    Compass,
    SensorItem,
    OSCDevice,
    ExifParameters,
    RecordingType)
from parsers.exif.utils import (
    ExifTags, CardinalDirection, SpeedUnit, SeaLevel,
    datetime_from_string,
    create_required_gps_tags,
    add_optional_gps_tags,
    add_gps_tags,
    dms_to_dd
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
        return self._exif_version(self.tags)

    def serialize(self):
        tags = None
        for item in self._sensors:
            gps = None
            compass = None
            if isinstance(item, PhotoMetadata):
                gps, compass = (item.gps, item.compass)
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

    # private methods

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
        gps.timestamp = self._gps_timestamp(tags_data)
        exif_timestamp = self._timestamp(tags_data)
        if (not gps.timestamp or
                (exif_timestamp is not None and exif_timestamp > 31556952
                 and abs(gps.timestamp - exif_timestamp) > 31556952)):
            # if there is no gps timestamp or gps timestamp differs with more than 1 year
            # compared to exif_timestamp we choose exif_timestamp
            gps.timestamp = exif_timestamp

        # required latitude and longitude
        gps.latitude = self._gps_latitude(tags_data)
        gps.longitude = self._gps_longitude(tags_data)
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
        photo.timestamp = self._timestamp(tags_data)
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
        ori_timestamp = self._timestamp(tags_data)
        device.timestamp = ori_timestamp if ori_timestamp is not None else self._gps_timestamp(tags_data)
        device.device_raw_name = self._device_model(tags_data)
        device.platform_name = self._maker_name(tags_data)
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

    @classmethod
    def _gps_compass(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        """Exif compass from gps_data represented by gps tags found in image exif.
        reference relative to true north"""
        if ExifTags.GPS_DIRECTION.value in gps_data:
            # compass exists
            compass_ratio = gps_data[ExifTags.GPS_DIRECTION.value].values[0]
            if ExifTags.GPS_DIRECTION_REF.value in gps_data and \
                    gps_data[ExifTags.GPS_DIRECTION_REF.value] == CardinalDirection.MAGNETIC_NORTH:
                # if we find magnetic north then we don't consider a valid compass
                return None
            return compass_ratio.num / compass_ratio.den
        # no compass found
        return None

    @classmethod
    def _gps_timestamp(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        """Exif gps time from gps_data represented by gps tags found in image exif.
        In exif there are values giving the hour, minute, and second.
        This is UTC time"""
        if ExifTags.GPS_TIMESTAMP.value in gps_data:
            # timestamp exists
            _timestamp = gps_data[ExifTags.GPS_TIMESTAMP.value]
            hours: Ratio = _timestamp.values[0]
            minutes: Ratio = _timestamp.values[1]
            seconds: Ratio = _timestamp.values[2]

            if hours.den == 0.0 or minutes.den == 0.0 or seconds.den == 0.0:
                return None

            day_timestamp = \
                hours.num / hours.den * 3600 + \
                minutes.num / minutes.den * 60 + \
                seconds.num / seconds.den

            if ExifTags.GPS_DATE_STAMP.value in gps_data:
                # this tag is the one present in the exif documentation
                # but from experience ExifTags.GPS_DATE is replacing this tag
                gps_date = gps_data[ExifTags.GPS_DATE_STAMP.value].values
                gps_date_time = datetime_from_string(gps_date, "%Y:%m:%d")
                if gps_date_time is None:
                    return None
                date_timestamp = gps_date_time.timestamp()

                return day_timestamp + date_timestamp

            if ExifTags.GPS_DATE.value in gps_data:
                # this tag is a replacement for ExifTags.GPS_DATE_STAMP
                gps_date = gps_data[ExifTags.GPS_DATE.value].values
                gps_date_time = datetime_from_string(gps_date, "%Y:%m:%d")
                if gps_date_time is None:
                    return None
                date_timestamp = gps_date_time.timestamp()

                return day_timestamp + date_timestamp

            # no date information only hour minutes second of day -> no valid gps timestamp
        # no gps timestamp found
        return None

    @classmethod
    def _timestamp(cls, tags: Dict[str, IfdTag]) -> Optional[float]:
        """Original timestamp determined by the digital still camera. This is timezone corrected."""
        if ExifTags.DATE_TIME_ORIGINAL.value in tags:
            date_taken = tags[ExifTags.DATE_TIME_ORIGINAL.value].values
            date_time_value = datetime_from_string(date_taken, "%Y:%m:%d %H:%M:%S")
            if date_time_value is None:
                return None
            _timestamp = date_time_value.timestamp()

            return _timestamp
        if ExifTags.DATE_TIME_DIGITIZED.value in tags:
            date_taken = tags[ExifTags.DATE_TIME_DIGITIZED.value].values
            date_time_value = datetime_from_string(date_taken, "%Y:%m:%d %H:%M:%S")
            if date_time_value is None:
                return None
            _timestamp = date_time_value.timestamp()

            return _timestamp
        # no timestamp information found
        return None

    @classmethod
    def _gps_altitude(cls, gps_tags: Dict[str, IfdTag]) -> Optional[float]:
        """GPS altitude form exif """
        if ExifTags.GPS_ALTITUDE.value in gps_tags:
            # altitude exists
            altitude_ratio = gps_tags[ExifTags.GPS_ALTITUDE.value].values[0]
            altitude = altitude_ratio.num / altitude_ratio.den
            if ExifTags.GPS_ALTITUDE_REF.value in gps_tags and \
                    gps_tags[ExifTags.GPS_ALTITUDE_REF.value] == SeaLevel.BELOW.value:
                altitude = -1 * altitude
            return altitude
        return None

    @classmethod
    def _gps_speed(cls, gps_tags: Dict[str, IfdTag]) -> Optional[float]:
        """Returns GPS speed from exif in km per hour or None if no gps speed tag found"""
        if ExifTags.GPS_SPEED.value in gps_tags:
            # gps speed exist
            speed_ratio = gps_tags[ExifTags.GPS_SPEED.value].values[0]
            speed = speed_ratio.num / speed_ratio.den
            if ExifTags.GPS_SPEED_REF.value in gps_tags:
                if gps_tags[ExifTags.GPS_SPEED_REF.value] == SpeedUnit.MPH.value:
                    speed = SpeedUnit.convert_mph_to_kmh(speed)
                if gps_tags[ExifTags.GPS_SPEED_REF.value] == SpeedUnit.KNOTS.value:
                    speed = SpeedUnit.convert_knots_to_kmh(speed)
            return speed
        # no gps speed tag found
        return None

    @classmethod
    def _maker_name(cls, tags: Dict[str, IfdTag]) -> Optional[str]:
        """this method returns a platform name"""
        device_make = None
        if ExifTags.DEVICE_MAKE.value in tags:
            device_make = str(tags[ExifTags.DEVICE_MAKE.value])

        return device_make

    @classmethod
    def _device_model(cls, tags: Dict[str, IfdTag]) -> Optional[str]:
        """this method returns a device name"""
        model = None
        if ExifTags.DEVICE_MODEL.value in tags:
            model = str(tags[ExifTags.DEVICE_MODEL.value])

        return model

    @classmethod
    def _exif_version(cls, tags: Dict[str, IfdTag]) -> Optional[str]:
        """this method returns exif version"""
        if ExifTags.FORMAT_VERSION.value in tags:
            return str(tags[ExifTags.FORMAT_VERSION.value])
        return None

    @classmethod
    def _gps_latitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        """Exif latitude from gps_data represented by gps tags found in image exif"""
        if ExifTags.GPS_LATITUDE.value in gps_data:
            # latitude exists
            dms_values = gps_data[ExifTags.GPS_LATITUDE.value]
            _latitude = dms_to_dd(dms_values)
            if _latitude is None:
                return None

            if ExifTags.GPS_LATITUDE_REF.value in gps_data and \
                    (str(gps_data[ExifTags.GPS_LATITUDE_REF.value]) == str(CardinalDirection.S.value)):
                # cardinal direction is S so the latitude should be negative
                _latitude = -1 * _latitude

            if abs(_latitude) > 90:
                return None

            return _latitude
        # no latitude info found
        return None

    @classmethod
    def _gps_longitude(cls, gps_data: Dict[str, IfdTag]) -> Optional[float]:
        """Exif longitude from gps_data represented by gps tags found in image exif"""
        if ExifTags.GPS_LONGITUDE.value in gps_data:
            # longitude exists
            dms_values = gps_data[ExifTags.GPS_LONGITUDE.value]
            _longitude = dms_to_dd(dms_values)
            if _longitude is None:
                return None

            if ExifTags.GPS_LONGITUDE_REF.value in gps_data and \
                    str(gps_data[ExifTags.GPS_LONGITUDE_REF.value]) == str(CardinalDirection.W.value):
                # cardinal direction is W so the longitude should be negative
                _longitude = -1 * _longitude

            if abs(_longitude) > 180:
                return None

            return _longitude
        # no longitude info found
        return None
