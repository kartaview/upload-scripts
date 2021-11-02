"""This file contains all the Metadata 1.x item parser definitions"""
from typing import Optional, Dict, Any

from common.models import SensorItem, Pressure, PhotoMetadata, OBD, DeviceMotion, Acceleration, GPS
from common.models import Attitude, Gravity, Compass


class ItemLegacyParser:
    """ItemLegacyParser is a parser class that can parse a Metadata1.x row and
    return a SensorItem"""

    # pylint: disable=R0913
    def __init__(self,
                 metadata_format,
                 item_class,
                 required_attributes_mapping,
                 optional_attributes_mapping=None,
                 post_processing=None):
        if optional_attributes_mapping is None:
            optional_attributes_mapping = {}

        self._metadata_format = metadata_format
        self._item_class = item_class
        self._attributes_element_names = required_attributes_mapping
        self._optional_attributes_element_names = optional_attributes_mapping
        self._post_processing = post_processing

    # pylint: enable=R0913

    def __eq__(self, other):
        if isinstance(other, ItemLegacyParser):
            return self == other
        return False

    def __hash__(self):
        return hash((self._item_class, self._metadata_format))

    def parse(self, elements) -> Optional[SensorItem]:
        """parse a list of elements"""
        # search for required attributes
        element_values: Dict[str, Any] = {}
        for _, element_name in self._attributes_element_names.items():
            name_value = self._value(elements, element_name)
            if not name_value:
                return None
            element_values[element_name] = name_value
        # set required attributes
        item_instance = self._item_class()
        self._set_values_for_attributes(element_values,
                                        self._attributes_element_names,
                                        item_instance)

        # set optional attributes
        element_values = {}
        for _, element_name in self._optional_attributes_element_names.items():
            name_value = self._value(elements, element_name)
            element_values[element_name] = name_value
        self._set_values_for_attributes(element_values,
                                        self._optional_attributes_element_names,
                                        item_instance)
        # make post processing
        if self._post_processing:
            self._post_processing(item_instance)

        return item_instance

    @classmethod
    def _set_values_for_attributes(cls, element_values, attributes_element_names, item_instance):
        for attribute_name, element_name in attributes_element_names.items():
            if "." in attribute_name:
                sub_attributes = attribute_name.split(".")
                # get the sub item that has the property that needs to be set
                tmp_item = item_instance
                for level in range(len(sub_attributes) - 1):
                    tmp_item = getattr(tmp_item, sub_attributes[level])
                setattr(tmp_item,
                        sub_attributes[len(sub_attributes)-1],
                        element_values[element_name])
            else:
                setattr(item_instance,
                        attribute_name,
                        element_values[element_name])

    def _value(self, elements, key):
        if key not in self._metadata_format:
            return None

        if elements[self._metadata_format[key]] != '':
            return elements[self._metadata_format[key]]
        return None


def timestamp_error(item: SensorItem):
    """this function fixes an error when timestamp is logged in a smaller unit then seconds."""
    if float(item.timestamp) / 3600 * 24 * 356 > 2019 and \
            "." not in str(item.timestamp) and \
            len(str(item.timestamp)) > 10:
        # this bug has fixed in 2018
        # 1471117570183 -> 1471117570.183
        item.timestamp = item.timestamp[:10] + "." + item.timestamp[10:]
    item.timestamp = float(item.timestamp)


def gps_parser(metadata_format, device_item):
    """gps parser"""
    def waylens_device(gps: GPS):
        """this function fixes an error for waylens metadata when gps speed is logged in m/s"""
        timestamp_error(gps)
        if "waylens" in device_item.device_raw_name:
            gps.speed = str(float(gps.speed) / 3.6)
        gps.latitude = float(gps.latitude)
        gps.longitude = float(gps.longitude)
        gps.horizontal_accuracy = float(gps.horizontal_accuracy)
        if gps.altitude is not None:
            gps.altitude = float(gps.altitude)
        if gps.vertical_accuracy is not None:
            gps.vertical_accuracy = float(gps.vertical_accuracy)
        if gps.speed is not None:
            gps.speed = float(gps.speed)

    return ItemLegacyParser(metadata_format,
                            GPS,
                            {"timestamp": "time",
                             "latitude": "latitude",
                             "longitude": "longitude",
                             "horizontal_accuracy": "horizontal_accuracy"},
                            {"altitude": "elevation",
                             "vertical_accuracy": "vertical_accuracy",
                             "gps_speed": "gps.speed"},
                            waylens_device)


def obd_parser(metadata_format):
    """OBD parser"""
    def type_conversions(obd: OBD):
        timestamp_error(obd)
        obd.speed = float(obd.speed)

    return ItemLegacyParser(metadata_format,
                            OBD,
                            {"timestamp": "time",
                             "speed": "OBDs"},
                            {},
                            type_conversions)


def pressure_parser(metadata_format):
    """pressure parser"""
    def type_conversions(pressure: Pressure):
        timestamp_error(pressure)
        pressure.pressure = float(pressure.pressure)

    return ItemLegacyParser(metadata_format,
                            Pressure,
                            {"timestamp": "time",
                             "pressure": "pressure"},
                            {},
                            type_conversions)


def compass_parser(metadata_format):
    """compass parser"""
    def type_conversions(compass: Compass):
        timestamp_error(compass)
        compass.compass = float(compass.compass)

    return ItemLegacyParser(metadata_format,
                            Compass,
                            {"timestamp": "time",
                             "compass": "compass"},
                            {},
                            type_conversions)


def attitude_parser(metadata_format):
    """attitude parser"""
    def type_conversions(attitude: Attitude):
        timestamp_error(attitude)
        attitude.yaw = float(attitude.yaw)
        attitude.pitch = float(attitude.pitch)
        attitude.roll = float(attitude.roll)

    return ItemLegacyParser(metadata_format,
                            Attitude,
                            {"timestamp": "time",
                             "yaw": "yaw",
                             "pitch": "pitch",
                             "roll": "roll"},
                            {},
                            type_conversions)


def gravity_parser(metadata_format):
    """gravity parser"""
    def type_conversions(gravity: Gravity):
        timestamp_error(gravity)
        gravity.acc_x = float(gravity.acc_x)
        gravity.acc_y = float(gravity.acc_y)
        gravity.acc_z = float(gravity.acc_z)

    return ItemLegacyParser(metadata_format,
                            Gravity,
                            {"timestamp": "time",
                             "acc_x": "gravity.x",
                             "acc_y": "gravity.y",
                             "acc_z": "gravity.z"},
                            {},
                            type_conversions)


def acceleration_parser(metadata_format):
    """acceleration parser"""
    def type_conversions(acceleration: Acceleration):
        timestamp_error(acceleration)
        acceleration.acc_x = float(acceleration.acc_x)
        acceleration.acc_y = float(acceleration.acc_y)
        acceleration.acc_z = float(acceleration.acc_z)

    return ItemLegacyParser(metadata_format,
                            Acceleration,
                            {"timestamp": "time",
                             "acc_x": "acceleration.x",
                             "acc_y": "acceleration.y",
                             "acc_z": "acceleration.z"},
                            {},
                            type_conversions)


def incomplete_photo_parser(metadata_format):
    """photo parser"""
    def type_conversions(photo_metadata: PhotoMetadata):
        timestamp_error(photo_metadata)
        if photo_metadata.video_index is not None:
            photo_metadata.video_index = int(photo_metadata.video_index)
        photo_metadata.frame_index = int(photo_metadata.frame_index)

    return ItemLegacyParser(metadata_format,
                            PhotoMetadata,
                            {"timestamp": "time",
                             "frame_index": "frame_index"},
                            {"video_index": "video_index"},
                            type_conversions)


def device_motion_parse(metadata_format):
    """device motion parser"""
    def type_conversions(device_motion: DeviceMotion):
        timestamp_error(device_motion)
        DeviceMotion.type_conversions(device_motion)

    return ItemLegacyParser(metadata_format,
                            DeviceMotion,
                            {"acceleration.acc_x": "acceleration.x",
                             "acceleration.acc_y": "acceleration.y",
                             "acceleration.acc_z": "acceleration.z",
                             "gravity.acc_x": "gravity.x",
                             "gravity.acc_y": "gravity.y",
                             "gravity.acc_z": "gravity.z",
                             "gyroscope.yaw": "yaw",
                             "gyroscope.pitch": "pitch",
                             "gyroscope.roll": "roll"},
                            {},
                            type_conversions)
