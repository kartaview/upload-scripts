import math
import datetime
from enum import Enum
from typing import Tuple, Any, Optional, List, Dict
import piexif
from exifread.classes import Ratio, IfdTag


MPH_TO_KMH_FACTOR = 1.60934
"""miles per hour to kilometers per hour conversion factor"""
KNOTS_TO_KMH_FACTOR = 1.852
"""knots to kilometers per hour conversion factor"""


class ExifTags(Enum):
    """This is a enumeration of exif tags. More info here
    http://owl.phy.queensu.ca/~phil/exiftool/TagNames/GPS.html """
    DATE_TIME_ORIGINAL = "EXIF DateTimeOriginal"
    DATE_TIME_DIGITIZED = "EXIF DateTimeDigitized"
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
    DESCRIPTION = "Image ImageDescription"


class CardinalDirection(Enum):
    """Exif Enum with all cardinal directions"""
    N = "N"
    S = "S"
    E = "E"
    W = "W"
    TRUE_NORTH = "T"
    MAGNETIC_NORTH = "M"


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


def gps_latitude(gps_data: Dict[str, IfdTag]) -> Optional[float]:
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


def gps_longitude(gps_data: Dict[str, IfdTag]) -> Optional[float]:
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


def gps_compass(gps_data: Dict[str, IfdTag]) -> Optional[float]:
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


def gps_timestamp(gps_data: Dict[str, IfdTag]) -> Optional[float]:
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


def timestamp(tags: Dict[str, IfdTag]) -> Optional[float]:
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


def datetime_from_string(date_taken, string_format):
    try:
        tmp = str(date_taken).replace("-", ":")
        time_value = datetime.datetime.strptime(tmp, string_format)
        if time_value.tzinfo is None:
            time_value = time_value.replace(tzinfo=datetime.timezone.utc)
        return time_value
    except ValueError as error:
        # this is are workarounds for wrong timestamp format e.g

        # date_taken = "????:??:?? ??:??:??"
        if isinstance(date_taken, str):
            return None

        # date_taken=b'\\xf2\\xf0\\xf1\\xf9:\\xf0\\xf4:\\xf0\\xf5 \\xf1\\xf1:\\xf2\\xf9:\\xf5\\xf4'
        try:
            date_taken = str(date_taken.decode("utf-8", "backslashreplace")).replace("\\xf", "")
            time_value = datetime.datetime.strptime(date_taken, string_format)
            if time_value.tzinfo is None:
                time_value = time_value.replace(tzinfo=datetime.timezone.utc)
            return time_value
        except ValueError:
            raise ValueError from error


def gps_altitude(gps_tags: Dict[str, IfdTag]) -> Optional[float]:
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


def gps_speed(gps_tags: Dict[str, IfdTag]) -> Optional[float]:
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


def maker_name(tags: Dict[str, IfdTag]) -> Optional[str]:
    """this method returns a platform name"""
    device_make = None
    if ExifTags.DEVICE_MAKE.value in tags:
        device_make = str(tags[ExifTags.DEVICE_MAKE.value])

    return device_make


def device_model(tags: Dict[str, IfdTag]) -> Optional[str]:
    """this method returns a device name"""
    model = None
    if ExifTags.DEVICE_MODEL.value in tags:
        model = str(tags[ExifTags.DEVICE_MODEL.value])

    return model


def exif_version(tags: Dict[str, IfdTag]) -> Optional[str]:
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


def create_required_gps_tags(timestamp_gps: Optional[float],
                             latitude: float,
                             longitude: float) -> Dict[str, Any]:
    """This method will creates gps required tags """
    exif_gps: Dict[str, Any] = {}
    if timestamp_gps is not None:
        day = int(timestamp_gps / 86400) * 86400
        hour = int((timestamp_gps - day) / 3600)
        minutes = int((timestamp_gps - day - hour * 3600) / 60)
        seconds = int(timestamp_gps - day - hour * 3600 - minutes * 60)

        day_timestamp_str = datetime.date.fromtimestamp(day).strftime("%Y:%m:%d")
        exif_gps[piexif.GPSIFD.GPSTimeStamp] = [(hour, 1),
                                                (minutes, 1),
                                                (seconds, 1)]
        exif_gps[piexif.GPSIFD.GPSDateStamp] = day_timestamp_str

    dms_latitude = __dd_to_dms(latitude)
    dms_longitude = __dd_to_dms(longitude)
    exif_gps[piexif.GPSIFD.GPSLatitudeRef] = "S" if latitude < 0 else "N"
    exif_gps[piexif.GPSIFD.GPSLatitude] = dms_latitude
    exif_gps[piexif.GPSIFD.GPSLongitudeRef] = "W" if longitude < 0 else "E"
    exif_gps[piexif.GPSIFD.GPSLongitude] = dms_longitude
    return exif_gps


def add_optional_gps_tags(exif_gps: Dict[str, Any],
                          speed: Optional[float],
                          altitude: Optional[float],
                          compass: Optional[float]):
    """This method will append optional tags to exif_gps tags dictionary"""
    precision = 10000
    if speed:
        exif_gps[piexif.GPSIFD.GPSSpeed] = (int(speed * precision), precision)
        exif_gps[piexif.GPSIFD.GPSSpeedRef] = SpeedUnit.KMH.value
    if altitude:
        exif_gps[piexif.GPSIFD.GPSAltitude] = (int(altitude * precision), precision)
        sea_level = SeaLevel.BELOW.value if altitude < 0 else SeaLevel.ABOVE.value
        exif_gps[piexif.GPSIFD.GPSAltitudeRef] = sea_level
    if compass:
        exif_gps[piexif.GPSIFD.GPSImgDirection] = (int(compass * precision), precision)
        exif_gps[piexif.GPSIFD.GPSImgDirectionRef] = CardinalDirection.TRUE_NORTH.value
