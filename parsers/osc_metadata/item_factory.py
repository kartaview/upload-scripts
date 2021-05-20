"""this file contains all item parsers for Metadata2.0"""
from typing import List

from common.models import *


class ItemParser:
    """ItemParser is a parser class that can parse a Metadata2.0 row and return a SensorItem"""
    def __init__(self, version: int,
                 formats: dict,
                 item_class,
                 item_name,
                 post_processing=None):
        self.version: int = version
        self.format: dict = formats
        self.item_class = item_class
        self.item_name = item_name
        self.post_processing = post_processing

    def __eq__(self, other):
        if isinstance(other, ItemParser):
            return self.version == other.version and \
                   self.format == other.format and \
                   self.item_class == other.item_class
        return False

    def __hash__(self):
        return hash((self.version, self.format, self.item_class))

    def parse(self, row, timestamp) -> Optional[SensorItem]:
        """This method will return a complete Metadata Item instance that was found at the row
        received as parameter"""
        _elements = row.replace("\n", "").split(";")
        if len(_elements) != len(self.format):
            return None

        item_instance = self.item_class()
        item_instance.timestamp = float(timestamp)
        for attribute_key, attribute_value in self.format.items():
            if "." in attribute_key:
                sub_attributes = attribute_key.split(".")
                # get the sub item that has the property that needs to be set
                tmp_item = item_instance
                for level in range(len(sub_attributes) - 1):
                    tmp_item = getattr(tmp_item, sub_attributes[level])
                setattr(tmp_item,
                        sub_attributes[len(sub_attributes) - 1],
                        ItemParser._value(_elements, attribute_value))

            else:
                setattr(item_instance,
                        attribute_key,
                        ItemParser._value(_elements, attribute_value))
        if self.post_processing is not None:
            self.post_processing(item_instance)

        return item_instance

    @classmethod
    def _value(cls, elements, key) -> Optional[str]:
        if elements[key] != '':
            return elements[key]
        return None


class SensorItemDefinition:
    """SensorItemDefinition is a model class for the Metadata2.0 header rows"""
    def __init__(self):
        self.alias = None
        self.item_name = None
        self.version = None
        self.min_compatible_version = None
        self.parsers: [ItemParser] = None

    def __eq__(self, other):
        if isinstance(other, SensorItemDefinition):
            return self.alias == other.alias and \
                   self.item_name == other.item_name and \
                   self.version == other.version and \
                   self.min_compatible_version == other.min_compatible_version and \
                   len(self.parsers) == len(other.parsers)
        return False

    def __hash__(self):
        return hash((self.alias,
                     self.item_name,
                     self.version,
                     self.min_compatible_version,
                     len(self.parsers)))

    @classmethod
    def definition_from_row(cls, row):
        """This method will return a SensorItemDefinition compatible with the row sent as
        parameter. If no compatible SensorItemDefinition is found then it will return None"""
        if ";" not in row or ":" not in row:
            return None
        elements = row.split(":")
        if len(elements) != 2:
            return None
        elements = elements[1].split(";")
        if len(elements) != 4:
            return None
        definition = SensorItemDefinition()
        definition.alias = elements[0]
        definition.item_name = elements[1]
        definition.version = elements[2]
        definition.min_compatible_version = elements[3]
        definition.parsers = _compatible_parser(definition)
        if not definition.parsers:
            return None
        # setting the definition on the first parser will set  class
        class_name = definition.parsers[0].item_class
        class_name.definition = definition

        return definition


def _available_parsers() -> List[ItemParser]:
    """This function returns all the available item parsers"""
    parsers = [photo_v1(),
               gps_v1(),
               acceleration_v1(),
               compass_v1(),
               obd_v1(),
               pressure_v1(),
               attitude_v1(),
               gravity_v1(),
               device_v1(),
               device_motion_v1(),
               camera_v1(),
               camera_v2(),
               exif_v1(),
               exif_v2()]
    return parsers


def _compatible_parser(definition: SensorItemDefinition) -> List[ItemParser]:
    """This function returns all the compatible item parsers for a specific
    SensorItemDefinition"""

    item_name = definition.item_name
    min_version = definition.min_compatible_version
    compatible = []
    for parser in _available_parsers():
        if parser.version >= int(min_version) and parser.item_name == item_name:
            compatible.append(parser)
    return compatible


def photo_v1():
    """This is a factory method that returns a item parser for version 1 of the photo row"""

    def type_conversions(photo_metadata: PhotoMetadata):
        photo_metadata.video_index = int(photo_metadata.video_index)
        photo_metadata.frame_index = int(photo_metadata.frame_index)
        photo_metadata.gps.timestamp = float(photo_metadata.gps.timestamp)
        photo_metadata.gps.latitude = float(photo_metadata.gps.latitude)
        photo_metadata.gps.longitude = float(photo_metadata.gps.longitude)
        photo_metadata.gps.horizontal_accuracy = float(photo_metadata.gps.horizontal_accuracy)
        photo_metadata.gps.speed = float(photo_metadata.gps.speed)

        if photo_metadata.obd.speed is not None and photo_metadata.obd.timestamp is not None:
            photo_metadata.obd.timestamp = float(photo_metadata.obd.timestamp)
            photo_metadata.obd.speed = float(photo_metadata.obd.speed)

        if photo_metadata.compass.compass is not None and photo_metadata.compass.timestamp is not None:
            photo_metadata.compass.compass = float(photo_metadata.compass.compass)
            photo_metadata.compass.timestamp = float(photo_metadata.compass.timestamp)

    photo_parser = ItemParser(1, {'video_index': 0,
                                  'frame_index': 1,
                                  'gps.timestamp': 2,
                                  'gps.latitude': 3,
                                  'gps.longitude': 4,
                                  'gps.horizontal_accuracy': 5,
                                  'gps.speed': 6,
                                  'compass.timestamp': 7,
                                  'compass.compass': 8,
                                  'obd.timestamp': 9,
                                  'obd.speed': 10},
                              PhotoMetadata,
                              "PHOTO",
                              type_conversions)

    return photo_parser


def gps_v1():
    """This is a factory method to get a ItemParser for the version 1 of the GPS found in
    Metadata format"""

    def type_conversions(gps: GPS):
        gps.latitude = float(gps.latitude)
        gps.longitude = float(gps.longitude)
        gps.altitude = float(gps.altitude)
        gps.horizontal_accuracy = float(gps.horizontal_accuracy)
        gps.vertical_accuracy = float(gps.vertical_accuracy)
        gps.speed = float(gps.speed)

    gps_parser = ItemParser(1, {'latitude': 0,
                                'longitude': 1,
                                'altitude': 2,
                                'horizontal_accuracy': 3,
                                'vertical_accuracy': 4,
                                'speed': 5},
                            GPS,
                            "GPS",
                            type_conversions)
    return gps_parser


def acceleration_v1() -> ItemParser:
    """This method is returns a Acceleration ItemParser for Acceleration row version 1"""

    def type_conversions(acceleration: Acceleration):
        acceleration.acc_x = float(acceleration.acc_x)
        acceleration.acc_y = float(acceleration.acc_y)
        acceleration.acc_z = float(acceleration.acc_z)

    parser = ItemParser(1, {'acc_x': 0,
                            'acc_y': 1,
                            'acc_z': 2},
                        Acceleration,
                        "ACCELERATION",
                        type_conversions)
    return parser


def compass_v1() -> ItemParser:
    """This method is returns a Compass ItemParser for Compass row version 1"""

    def type_conversions(compass: Compass):
        compass.compass = float(compass.compass)

    parser = ItemParser(1, {'compass': 0}, Compass, "COMPASS", type_conversions)
    return parser


def obd_v1() -> ItemParser:
    """This method is returns a OBD ItemParser for OBD row version 1"""

    def type_conversions(obd: OBD):
        obd.speed = float(obd.speed)

    parser = ItemParser(1, {'speed': 0}, OBD, "OBD", type_conversions)
    return parser


def pressure_v1() -> ItemParser:
    """This method is returns a Pressure ItemParser for Pressure row version 1"""

    def type_conversions(pressure: Pressure):
        pressure.pressure = float(pressure.pressure)

    parser = ItemParser(1, {'pressure': 0}, Pressure, "PRESSURE", type_conversions)
    return parser


def attitude_v1() -> ItemParser:
    """This method is returns a Attitude ItemParser for Attitude row version 1"""

    def type_conversions(attitude: Attitude):
        attitude.yaw = float(attitude.yaw)
        attitude.pitch = float(attitude.pitch)
        attitude.roll = float(attitude.roll)

    parser = ItemParser(1, {'yaw': 0,
                            'pitch': 1,
                            'roll': 2},
                        Attitude, "ATTITUDE",
                        type_conversions)
    return parser


def gravity_v1() -> ItemParser:
    """This method is returns a Gravity ItemParser for Gravity row version 1"""

    def type_conversions(gravity: Gravity):
        gravity.acc_x = float(gravity.acc_x)
        gravity.acc_y = float(gravity.acc_y)
        gravity.acc_z = float(gravity.acc_z)

    parser = ItemParser(1, {'acc_x': 0,
                            'acc_y': 1,
                            'acc_z': 2},
                        Gravity, "GRAVITY",
                        type_conversions)
    return parser


def device_motion_v1() -> ItemParser:
    """This method is returns a DeviceMotion ItemParser for DeviceMotion row version 1"""

    def type_conversions(device_motion: DeviceMotion):
        device_motion.acceleration.acc_x = float(device_motion.acceleration.acc_x)
        device_motion.acceleration.acc_y = float(device_motion.acceleration.acc_y)
        device_motion.acceleration.acc_z = float(device_motion.acceleration.acc_z)
        device_motion.gravity.acc_x = float(device_motion.gravity.acc_x)
        device_motion.gravity.acc_y = float(device_motion.gravity.acc_y)
        device_motion.gravity.acc_z = float(device_motion.gravity.acc_z)
        device_motion.gyroscope.yaw = float(device_motion.gyroscope.yaw)
        device_motion.gyroscope.pitch = float(device_motion.gyroscope.pitch)
        device_motion.gyroscope.roll = float(device_motion.gyroscope.roll)

    parser = ItemParser(1, {'gyroscope.yaw': 0,
                            'gyroscope.pitch': 1,
                            'gyroscope.roll': 2,
                            'acceleration.acc_x': 3,
                            'acceleration.acc_y': 4,
                            'acceleration.acc_z': 5,
                            'gravity.acc_x': 6,
                            'gravity.acc_y': 7,
                            'gravity.acc_z': 8},
                        DeviceMotion, "DEVICEMOTION",
                        type_conversions)
    return parser


def device_v1() -> ItemParser:
    """This method is returns a OSCDevice ItemParser for OSCDevice row version 1"""

    def type_conversions(device: OSCDevice):
        if "photo" in device.recording_type:
            device.recording_type = RecordingType.PHOTO
        elif "video" in device.recording_type:
            device.recording_type = RecordingType.VIDEO
        else:
            device.recording_type = RecordingType.UNKNOWN

    parser = ItemParser(1, {'platform_name': 0,
                            'os_raw_name': 1,
                            'os_version': 2,
                            'device_raw_name': 3,
                            'app_version': 4,
                            'app_build_number': 5,
                            'recording_type': 6},
                        OSCDevice, "DEVICE",
                        type_conversions)
    return parser


def camera_v1() -> ItemParser:
    """This method is returns a CameraParameters ItemParser for CameraParameters row
            version 1"""
    def type_conversion(camera: CameraParameters):
        camera.h_fov = float(camera.h_fov)
        camera.v_fov = None  # TODO: Compute v_fov based on h_fov and resolution

    parser = ItemParser(1, {'h_fov': 0,
                            'v_fov': 1,
                            'aperture': 2},
                        CameraParameters, "CAMERA", type_conversion)

    return parser


def camera_v2() -> ItemParser:
    """This method is returns a CameraParameters ItemParser for CameraParameters row
            version 2 like hFoV;vFoV;aperture """
    def type_conversion(camera: CameraParameters):
        camera.h_fov = float(camera.h_fov)
        camera.v_fov = float(camera.v_fov)

    parser = ItemParser(2, {'h_fov': 0,
                            'v_fov': 1,
                            'aperture': 2},
                        CameraParameters, "CAMERA", type_conversion)
    return parser


def exif_v1() -> ItemParser:
    """This method is returns a ExifParameters ItemParser for ExifParameters row version 1"""
    def type_conversion(exif: ExifParameters):
        exif.focal_length = float(exif.focal_length)

    parser = ItemParser(1, {'focal_length': 1},
                        ExifParameters, "EXIF", type_conversion)
    return parser


def exif_v2() -> ItemParser:
    """This method is returns a ExifParameters ItemParser for ExifParameters row version 2"""
    def type_conversion(exif: ExifParameters):
        exif.focal_length = float(exif.focal_length)
        exif.width = int(exif.width)
        exif.height = int(exif.height)

    parser = ItemParser(2, {'focal_length': 0,
                            'width': 1,
                            'height': 2},
                        ExifParameters, "EXIF", type_conversion)
    return parser
