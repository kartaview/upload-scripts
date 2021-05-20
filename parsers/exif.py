"""Module responsible to parse Exif information from a image"""
import math
import datetime
import os
from enum import Enum
from typing import Optional, Dict, List, Tuple, Any, Type
# third party
import exifread
import piexif

from common.models import PhotoMetadata, GPS, Compass, SensorItem, OSCDevice, ExifParameters, \
    RecordingType
from io_storage.storage import Storage
from parsers.base import BaseParser

# <editor-fold desc="Exif processing">

MPH_TO_KMH_FACTOR = 1.60934
"""miles per hour to kilometers per hour conversion factor"""
KNOTS_TO_KMH_FACTOR = 1.852
"""knots to kilometers per hour conversion factor"""


class ExifTags(Enum):
    """This is a enumeration of exif tags. More info here
    http://owl.phy.queensu.ca/~phil/exiftool/TagNames/GPS.html """
    DATE_TIME_ORIGINAL = "EXIF DateTimeOriginal"
    DATE_Time_DIGITIZED = "EXIF DateTimeDigitized"
    # latitude
    GPS_LATITUDE = "GPS GPSLatitude"
    GPS_LATITUDE_REF = "GPS GPSLatitudeRef"
    # longitude
    GPS_LONGITUDE = "GPS GPSLongitude"
    GPS_LONGITUDE_REF = "GPS GPSLongitudeRef"
    # altitude
    GPS_ALTITUDE_REF = "GPS GPSAltitudeRef"
    GPS_ALTITUDE = "GPS GPSAltitude"
    # timestamp
    GPS_TIMESTAMP = "GPS GPSTimeStamp"
    GPS_DATE_STAMP = "GPS GPSDateStamp"
    GPS_DATE = "GPS GPSDate"
    # speed
    GPS_SPEED_REF = "GPS GPSSpeedRef"
    GPS_SPEED = "GPS GPSSpeed"
    # direction
    GPS_DIRECTION_REF = "GPS GPSImgDirectionRef"
    GPS_DIRECTION = "GPS GPSImgDirection"
    # device name
    DEVICE_MAKE = "Image Make"
    DEVICE_MODEL = "Image Model"
    FORMAT_VERSION = "EXIF ExifVersion"
    WIDTH = "Image ImageWidth"
    HEIGHT = "Image ImageLength"


class CardinalDirection(Enum):
    """Exif Enum with all cardinal directions"""
    N = "N"
    S = "S"
    E = "E"
    W = "W"
    TrueNorth = "T"
    MagneticNorth = "M"


class SeaLevel(Enum):
    """Exif Enum
    If the reference is sea level and the
    altitude is above sea level, 0 is given.
    If the altitude is below sea level, a value of 1 is given and
    the altitude is indicated as an absolute value in the GPSAltitude tag.
    The reference unit is meters. Note that this tag is BYTE type,
     unlike other reference tags."""
    ABOVE = 0
    BELOW = 1


class SpeedUnit(Enum):
    """Exif speed unit enum"""
    KMH = "K"
    MPH = "M"
    KNOTS = "N"

    @classmethod
    def convert_mph_to_kmh(cls, mph) -> float:
        """This method converts from miles per hour to kilometers per hour"""
        return mph * MPH_TO_KMH_FACTOR

    @classmethod
    def convert_knots_to_kmh(cls, knots) -> float:
        """This method converts from knots to kilometers per hour"""
        return knots * KNOTS_TO_KMH_FACTOR


def __dms_to_dd(dms_value) -> Optional[float]:
    """DMS is Degrees Minutes Seconds, DD is Decimal Degrees.
             A typical format would be dd/1,mm/1,ss/1.
             When degrees and minutes are used and, for example,
             fractions of minutes are given up to two decimal places,
             the format would be dd/1,mmmm/100,0/1 """
    # degrees
    degrees_nominator = dms_value.values[0].num
    degrees_denominator = dms_value.values[0].den
    if float(degrees_denominator) == 0.0:
        return None
    degrees = float(degrees_nominator) / float(degrees_denominator)
    # minutes
    minutes_nominator = dms_value.values[1].num
    minutes_denominator = dms_value.values[1].den
    if float(minutes_denominator) == 0.0:
        return None
    minutes = float(minutes_nominator) / float(minutes_denominator)
    # seconds
    seconds_nominator = dms_value.values[2].num
    seconds_denominator = dms_value.values[2].den
    if float(seconds_denominator) == 0.0:
        return None
    seconds = float(seconds_nominator) / float(seconds_denominator)
    # decimal degrees
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def __dd_to_dms(decimal_degree) -> List[Tuple[float, int]]:
    decimal_degree_abs = abs(decimal_degree)

    degrees = math.floor(decimal_degree_abs)
    minute_float = (decimal_degree_abs - degrees) * 60
    minute = math.floor(minute_float)
    seconds = round((minute_float - minute) * 60 * 100)

    return [(degrees, 1), (minute, 1), (seconds, 100)]


def gps_latitude(gps_data: Dict[str, str]) -> Optional[float]:
    """Exif latitude from gps_data represented by gps tags found in image exif"""
    if ExifTags.GPS_LATITUDE.value in gps_data:
        # latitude exists
        dms_values = gps_data[ExifTags.GPS_LATITUDE.value]
        _latitude = __dms_to_dd(dms_values)
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


def gps_longitude(gps_data: Dict[str, str]) -> Optional[float]:
    """Exif longitude from gps_data represented by gps tags found in image exif"""
    if ExifTags.GPS_LONGITUDE.value in gps_data:
        # longitude exists
        dms_values = gps_data[ExifTags.GPS_LONGITUDE.value]
        _longitude = __dms_to_dd(dms_values)
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


def gps_compass(gps_data: Dict[str, str]) -> Optional[float]:
    """Exif compass from gps_data represented by gps tags found in image exif.
    reference relative to true north"""
    if ExifTags.GPS_DIRECTION.value in gps_data:
        # compass exists
        compass_ratio = gps_data[ExifTags.GPS_DIRECTION.value].values[0]
        if ExifTags.GPS_DIRECTION_REF.value in gps_data and \
                gps_data[ExifTags.GPS_DIRECTION_REF.value] == CardinalDirection.MagneticNorth:
            # if we find magnetic north then we don't consider a valid compass
            return None
        return compass_ratio.num / compass_ratio.den
    # no compass found
    return None


def gps_timestamp(gps_data: Dict[str, str]) -> Optional[float]:
    """Exif gps time from gps_data represented by gps tags found in image exif.
    In exif there are values giving the hour, minute, and second.
    This is UTC time"""
    if ExifTags.GPS_TIMESTAMP.value in gps_data:
        # timestamp exists
        _timestamp = gps_data[ExifTags.GPS_TIMESTAMP.value]
        hours: exifread.Ratio = _timestamp.values[0]
        minutes: exifread.Ratio = _timestamp.values[1]
        seconds: exifread.Ratio = _timestamp.values[2]

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
        return None
    # no gps timestamp found
    return None


def timestamp(tags: Dict[str, str]) -> Optional[float]:
    """Original timestamp determined by the digital still camera. This is timezone corrected."""
    if ExifTags.DATE_TIME_ORIGINAL.value in tags:
        date_taken = tags[ExifTags.DATE_TIME_ORIGINAL.value].values
        date_time_value = datetime_from_string(date_taken, "%Y:%m:%d %H:%M:%S")
        if date_time_value is None:
            return None
        _timestamp = date_time_value.timestamp()

        return _timestamp
    if ExifTags.DATE_Time_DIGITIZED.value in tags:
        date_taken = tags[ExifTags.DATE_Time_DIGITIZED.value].values
        date_time_value = datetime_from_string(date_taken, "%Y:%m:%d %H:%M:%S")
        if date_time_value is None:
            return None
        _timestamp = date_time_value.timestamp()

        return _timestamp
    # no timestamp information found
    return None


def datetime_from_string(date_taken, string_format):
    try:
        tmp = str(date_taken).replace("-", ":")
        dt = datetime.datetime.strptime(tmp, string_format)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError as e:
        # this is are workarounds for wrong timestamp format e.g

        # date_taken = "????:??:?? ??:??:??"
        if isinstance(date_taken, str):
            return None

        # date_taken=b'\\xf2\\xf0\\xf1\\xf9:\\xf0\\xf4:\\xf0\\xf5 \\xf1\\xf1:\\xf2\\xf9:\\xf5\\xf4'
        try:
            date_taken = str(date_taken.decode("utf-8", "backslashreplace")).replace("\\xf", "")
            dt = datetime.datetime.strptime(date_taken, string_format)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except ValueError:
            raise e


def gps_altitude(gps_tags: Dict[str, str]) -> Optional[float]:
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


def gps_speed(gps_tags: Dict[str, str]) -> Optional[float]:
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


def maker_name(tags: Dict[str, str]) -> Optional[str]:
    """this method returns a platform name"""
    device_make = None
    if ExifTags.DEVICE_MAKE.value in tags:
        device_make = str(tags[ExifTags.DEVICE_MAKE.value])

    return device_make


def device_model(tags: Dict[str, str]) -> Optional[str]:
    """this method returns a device name"""
    model = None
    if ExifTags.DEVICE_MODEL.value in tags:
        model = str(tags[ExifTags.DEVICE_MODEL.value])

    return model


def exif_version(tags: Dict[str, str]) -> Optional[str]:
    """this method returns exif version"""
    if ExifTags.FORMAT_VERSION.value in tags:
        return tags[ExifTags.FORMAT_VERSION.value]
    return None


def add_gps_tags(path: str, gps_tags: Dict[str, Any]):
    """This method will add gps tags to the photo found at path"""
    exif_dict = piexif.load(path)
    for tag, tag_value in gps_tags.items():
        exif_dict["GPS"][tag] = tag_value
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, path)


def create_required_gps_tags(timestamp_gps: float,
                             latitude: float,
                             longitude: float) -> Dict[str, Any]:
    """This method will creates gps required tags """
    exif_gps = {}
    dms_latitude = __dd_to_dms(latitude)
    dms_longitude = __dd_to_dms(longitude)
    day = int(timestamp_gps / 86400) * 86400
    hour = int((timestamp_gps - day) / 3600)
    minutes = int((timestamp_gps - day - hour * 3600) / 60)
    seconds = int(timestamp_gps - day - hour * 3600 - minutes * 60)

    day_timestamp_str = datetime.date.fromtimestamp(day).strftime("%Y:%m:%d")
    exif_gps[piexif.GPSIFD.GPSTimeStamp] = [(hour, 1),
                                            (minutes, 1),
                                            (seconds, 1)]
    exif_gps[piexif.GPSIFD.GPSDateStamp] = day_timestamp_str
    exif_gps[piexif.GPSIFD.GPSLatitudeRef] = "S" if latitude < 0 else "N"
    exif_gps[piexif.GPSIFD.GPSLatitude] = dms_latitude
    exif_gps[piexif.GPSIFD.GPSLongitudeRef] = "W" if longitude < 0 else "E"
    exif_gps[piexif.GPSIFD.GPSLongitude] = dms_longitude
    return exif_gps


def add_optional_gps_tags(exif_gps: Dict[str, Any],
                          speed: Optional[float],
                          altitude: Optional[float],
                          compass: Optional[float]) -> Dict[str, Any]:
    """This method will append optional tags to exif_gps tags dictionary"""
    if speed:
        exif_gps[piexif.GPSIFD.GPSSpeed] = (speed, 1)
        exif_gps[piexif.GPSIFD.GPSSpeedRef] = SpeedUnit.KMH.value
    if altitude:
        exif_gps[piexif.GPSIFD.GPSAltitude] = (altitude, 1)
        sea_level = SeaLevel.BELOW.value if altitude < 0 else SeaLevel.ABOVE.value
        exif_gps[piexif.GPSIFD.GPSAltitudeRef] = sea_level
    if compass:
        exif_gps[piexif.GPSIFD.GPSImgDirection] = (compass, 1)
        exif_gps[piexif.GPSIFD.GPSImgDirectionRef] = CardinalDirection.TrueNorth.value


# </editor-fold>


class ExifParser(BaseParser):
    """This class is a BaseParser that can parse images having exif"""

    def __init__(self, file_path, storage: Storage):
        super().__init__(file_path, storage)
        self._data_pointer = 0
        self._body_pointer = 0
        self.tags = self._all_tags()

    @classmethod
    def valid_parser(cls, file_path: str, storage: Storage):
        """this method will return a valid parser"""
        return ExifParser(file_path, storage)

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
        return [self._photo_item(self.tags),
                self._gps_item(self.tags),
                self._compass_item(self.tags),
                self._device_item(self.tags),
                self._exif_item(self.tags)]

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

    def compatible_sensors(self):
        return [PhotoMetadata, GPS, Compass, OSCDevice]

    # <editor-fold desc="Private methods">
    @classmethod
    def _gps_compass(cls, photo_metadata: PhotoMetadata):
        gps = photo_metadata.gps
        compass = photo_metadata.compass
        return gps, compass

    def _all_tags(self) -> Dict[str, str]:
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
            # if there is no gps timestamp or gps timestamp differs with more then 1 year compared to exif_timestamp we
            # choose exif_timestamp
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

        photo = PhotoMetadata()
        gps = self._gps_item(tags_data)
        if gps is None:
            return None

        photo.gps = gps
        compass = self._compass_item(tags_data)
        photo.compass = compass if compass is not None else Compass()
        photo.timestamp = timestamp(tags_data)
        file_name = os.path.basename(self.file_path)
        if file_name.isdigit():
            photo.frame_index = int(file_name)
        if photo.gps is not None:
            photo.timestamp = photo.gps.timestamp if photo.timestamp is None else photo.timestamp
            return photo
        return None

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

        return None

    # </editor-fold>
