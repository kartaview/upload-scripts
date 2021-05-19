"""This file will contain all common models"""
from enum import Enum
from typing import Optional


class RecordingType(Enum):
    """This enum represents all possible visual data types."""
    UNKNOWN = 0
    PHOTO = 1
    VIDEO = 2
    RAW = 3

    def __eq__(self, other):
        if isinstance(other, RecordingType):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)


class SensorItem:
    """This is a model class representing a generic data item"""

    def __init__(self):
        # value is always specified in seconds having sub-millisecond precision.
        self.timestamp: Optional[float] = None

    def __eq__(self, other):
        if isinstance(other, SensorItem):
            return self.timestamp == other.timestamp
        return False

    def __hash__(self):
        return hash(self.timestamp)


class PhotoMetadata(SensorItem):
    """PhotoMetadata is a SensorItem that represents a photo"""

    def __init__(self):
        super().__init__()
        self.gps: GPS = GPS()
        self.obd: OBD = OBD()
        self.compass: Compass = Compass()
        # index of the video in witch the PhotoMetadata has the corresponding image data.
        self.video_index: Optional[int] = None
        # frame index of the PhotoMetadata relative to the entire sequence of photos.
        self.frame_index: Optional[int] = None

    def __eq__(self, other):
        if isinstance(other, PhotoMetadata):
            return self.timestamp == other.timestamp and \
                   self.gps.latitude == other.gps.latitude and \
                   self.gps.longitude == other.gps.longitude and \
                   self.video_index == other.video_index and \
                   self.frame_index == other.frame_index
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.gps.latitude,
                     self.gps.longitude,
                     self.video_index,
                     self.frame_index))


class GPS(SensorItem):
    """GPS is a SensorItem model class that can represent all information found in a GPS item"""

    def __init__(self):
        super().__init__()
        # in degrees
        self.latitude: Optional[float] = None
        self.longitude: Optional[float] = None
        # in meters
        self.altitude: Optional[float] = None
        # in meters
        self.horizontal_accuracy: Optional[float] = None
        # in meters
        self.vertical_accuracy: Optional[float] = None
        # speed is in m/s
        self.speed: Optional[float] = None

    def __eq__(self, other):
        if isinstance(other, GPS):
            return self.timestamp == other.timestamp and \
                   self.latitude == other.latitude and \
                   self.longitude == other.longitude
        return False

    def __hash__(self):
        return hash((self.timestamp, self.latitude, self.longitude))

    def __str__(self):
        return "[{:f} : ({:.15f}, {:.15f})]".format(self.timestamp, self.longitude, self.latitude)


class Acceleration(SensorItem):
    """Acceleration is a SensorItem model representing an acceleration data"""

    def __init__(self):
        super().__init__()
        # X-axis acceleration in G's
        self.acc_x: Optional[float] = None
        # Y-axis acceleration in G's
        self.acc_y: Optional[float] = None
        # Z-axis acceleration in G's
        self.acc_z: Optional[float] = None

    def __eq__(self, other):
        if isinstance(other, Acceleration):
            return self.timestamp == other.timestamp and \
                   self.acc_x == other.acc_x and \
                   self.acc_y == other.acc_y and \
                   self.acc_z == other.acc_z
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.acc_x,
                     self.acc_y,
                     self.acc_z))


class Compass(SensorItem):
    """Compass is a SensorItem model class that can represent a compass data"""

    def __init__(self):
        super().__init__()
        # The heading (measured in degrees) relative to true north
        self.compass: Optional[float] = None

    def __eq__(self, other):
        if isinstance(other, Compass):
            return self.timestamp == other.timestamp and \
                   self.compass == other.compass
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.compass))


class OBD(SensorItem):
    """OBD is a SensorItem model class that can represent an obd data"""

    def __init__(self):
        super().__init__()
        # value is in km/h
        self.speed: Optional[float] = None

    def __eq__(self, other):
        if isinstance(other, OBD):
            return self.timestamp == other.timestamp and \
                   self.speed == other.speed
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.speed))


class Pressure(SensorItem):
    """Pressure is a SensorItem model class that can represent an pressure data"""

    def __init__(self):
        super().__init__()
        # value is in kPa
        self.pressure: Optional[float] = None

    def __eq__(self, other):
        if isinstance(other, Pressure):
            return self.timestamp == other.timestamp and \
                   self.pressure == other.pressure
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.pressure))


class Attitude(SensorItem):
    """Attitude is a SensorItem model class that can represent an attitude data"""

    def __init__(self):
        super().__init__()
        # Returns the yaw of the device in radians.
        self.yaw: Optional[float] = None
        # Returns the pitch of the device in radians.
        self.pitch: Optional[float] = None
        # Returns the roll of the device in radians.
        self.roll: Optional[float] = None

    def __eq__(self, other):
        if isinstance(other, Attitude):
            return self.timestamp == other.timestamp and \
                   self.yaw == other.yaw and \
                   self.pitch == other.pitch and \
                   self.roll == other.roll
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.yaw,
                     self.pitch,
                     self.roll))


class Gravity(Acceleration):
    """Gravity is a SensorItem model class that can represent a gravity data"""

    def __eq__(self, other):
        if isinstance(other, Gravity):
            return self.timestamp == other.timestamp and \
                   self.acc_x == other.acc_x and \
                   self.acc_y == other.acc_y and \
                   self.acc_z == other.acc_z
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.acc_x,
                     self.acc_y,
                     self.acc_z))


class DeviceMotion(SensorItem):
    """DeviceMotion is a SensorItem model class that can represent a device motion data"""

    def __init__(self):
        super().__init__()
        # Returns the attitude of the device.
        self.gyroscope: Attitude = Attitude()
        # Returns the acceleration that the user is giving to the device. Note
        # that the total acceleration of the device is equal to gravity plus
        # acceleration.
        self.acceleration: Acceleration = Acceleration()
        # Returns the gravity vector expressed in the device's reference frame. Note
        # that the total acceleration of the device is equal to gravity plus
        # acceleration.
        self.gravity: Gravity = Gravity()

    def __eq__(self, other):
        if isinstance(other, DeviceMotion):
            return self.timestamp == other.timestamp and \
                   self.gyroscope == other.gyroscope and \
                   self.acceleration == other.acceleration and \
                   self.gravity == other.gravity
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.gyroscope,
                     self.acceleration,
                     self.gravity))


class OSCDevice(SensorItem):
    """OSCDevice is a SensorItem model class that can represent an device data"""

    def __init__(self):
        super().__init__()
        # The platform from which the track was recorded:
        self.platform_name: Optional[str] = None
        # Custom version of operating system. Default OS name (platform) will be used if there is
        # no customized version. Ex: iOS, Yun OS, Paranoid Android
        self.os_raw_name: Optional[str] = None
        # The OS version from the device from which the track was recorded.
        self.os_version: Optional[str] = None
        # The raw name of the device. Eg: iPhone10,3 for iPhone X.
        self.device_raw_name: Optional[str] = None
        # App version with X.Y or X.Y.Z format. Eg: 2.4, 2.4.1
        self.app_version: Optional[str] = None
        # Build number for app version.
        self.app_build_number: Optional[str] = None
        # The type of recording: video, photo
        self.recording_type: Optional[RecordingType] = None

    def __eq__(self, other):
        if isinstance(other, OSCDevice):
            return self.timestamp == other.timestamp and \
                   self.platform_name == other.platform_name and \
                   self.os_raw_name == other.os_raw_name and \
                   self.os_version == other.os_version and \
                   self.device_raw_name == other.device_raw_name and \
                   self.app_version == other.app_version and \
                   self.app_build_number == other.app_build_number and \
                   self.recording_type == other.recording_type
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.platform_name,
                     self.os_raw_name,
                     self.os_version,
                     self.device_raw_name,
                     self.app_version,
                     self.app_build_number,
                     self.recording_type))


class CameraParameters(SensorItem):
    """CameraParameters is a SensorItem model class that can represent camera parameters"""

    def __init__(self):
        super().__init__()
        # Horizontal field of view in degrees. If field of view is unknown, a value of 0 is returned.
        self.h_fov: Optional[float] = None
        # Vertical field of view in degrees. If field of view is unknown, a value of 0 is returned.
        self.v_fov: Optional[float] = None
        # Aperture of the device.
        self.aperture: Optional[str] = None
        self.projection: Optional[CameraProjection] = None

    def __eq__(self, other):
        if isinstance(other, CameraParameters):
            return self.timestamp == other.timestamp and \
                   self.v_fov == other.v_fov and \
                   self.h_fov == other.h_fov and \
                   self.aperture == other.aperture and \
                   self.projection == other.projection
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.h_fov,
                     self.v_fov,
                     self.aperture))


class ExifParameters(SensorItem):
    """ExifParameters is a SensorItem model class that can represent a focal and f number"""

    def __init__(self):
        super().__init__()
        self.focal_length: Optional[float] = None
        self.width: Optional[int] = None
        self.height: Optional[int] = None

    def __eq__(self, other):
        if isinstance(other, ExifParameters):
            return self.timestamp == other.timestamp and \
                   self.focal_length == other.focal_length
        return False

    def __hash__(self):
        return hash((self.timestamp,
                     self.focal_length))


class CameraProjection(Enum):
    EQUIRECTANGULAR = "equirectangular"
    DUAL_FISHEYE = "DUAL_FISHEYE"
    FISHEYE_BACK = "FISHEYE_BACK"
    FISHEYE_FRONT = "FISHEYE_FRONT"
    PLAIN = "plain"


def projection_type_from_name(projection_name) -> Optional[CameraProjection]:
    projection = None
    if CameraProjection.PLAIN.name.lower() in projection_name.lower():
        projection = CameraProjection.PLAIN
    elif CameraProjection.EQUIRECTANGULAR.name.lower() in projection_name.lower():
        projection = CameraProjection.EQUIRECTANGULAR
    elif CameraProjection.DUAL_FISHEYE.name.lower() in projection_name.lower():
        projection = CameraProjection.DUAL_FISHEYE
    elif CameraProjection.FISHEYE_FRONT.name.lower() in projection_name.lower():
        projection = CameraProjection.FISHEYE_FRONT
    elif CameraProjection.FISHEYE_BACK.name.lower() in projection_name.lower():
        projection = CameraProjection.FISHEYE_BACK
    return projection
