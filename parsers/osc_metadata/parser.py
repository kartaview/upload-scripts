"""This module is made to parse osc metadata file version 2"""
from typing import Optional, Dict, List, Tuple, Type

from common.models import SensorItem, PhotoMetadata, ExifParameters, Attitude, Acceleration
from common.models import Compass, CameraParameters, DeviceMotion, OBD, GPS, Pressure, Gravity
from common.models import RecordingType, OSCDevice
from io_storage.storage import Storage

from parsers.base import BaseParser
from parsers.osc_metadata.item_factory import SensorItemDefinition, ItemParser
import parsers.osc_metadata.legacy_item_factory as legacy
from parsers.osc_metadata.legacy_item_factory import ItemLegacyParser


class MetadataParser(BaseParser):
    """MetadataParser is a BaseParser class capable of parsing a Metadata File compatible with the
        known SensorItem versions"""

    def __init__(self, file_path, storage: Storage):
        super().__init__(file_path, storage)
        self._data_pointer = 0
        self._body_pointer = 0
        self._device_item: Optional[OSCDevice] = None
        self._metadata_version = None
        self._alias_definitions: Dict[str, SensorItemDefinition] = {}
        self._configure_headers()

    def format_version(self) -> Optional[str]:
        """According to the documentation the version is found in the first line
        eg. METADATA:2.0"""
        if self._metadata_version is not None:
            return self._metadata_version

        if "METADATA:" not in self.header_line:
            return None

        header_elements = self.header_line.split(":")
        if len(header_elements) != 2:
            return None

        return header_elements[1]

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        """this method returns the next item found in the current metadata file
        that is an instance item_class"""
        definition = self._compatible_definition(item_class)
        if not definition:
            return None

        with self._storage.open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            item = None
            line = metadata_file.readline()
            while line and "END" not in line:
                timestamp, alias, item_data = self._timestamp_alias_data_from_row(line)
                if alias == definition.alias:
                    item_parser = definition.parsers[0]
                    item = item_parser.parse(item_data, timestamp)
                    break
                line = metadata_file.readline()
            self._data_pointer = metadata_file.tell()
            return item

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        """this method returns all items from the current metadata file that
        are instances of item_class"""
        definition = self._compatible_definition(item_class)
        if not definition:
            return []
        alias = definition.alias

        with self._storage.open(self.file_path) as metadata_file:
            metadata_file.seek(self._body_pointer)
            item_instances = []
            for line in metadata_file:
                name = ":" + alias + ":"
                if name in line:
                    timestamp, _, item_data = self._timestamp_alias_data_from_row(line)
                    row_parser = definition.parsers[0]
                    item_instance = row_parser.parse(item_data, timestamp)
                    item_instances.append(item_instance)
            return item_instances

    def next_item(self):
        """this method returns the next metadata item found in the current metadata file"""
        with self._storage.open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            line = metadata_file.readline()
            if "END" in line:
                return None
            timestamp, alias, item_data = self._timestamp_alias_data_from_row(line)
            definition = self._alias_definitions[alias]
            parser = definition.parsers[0]
            self._data_pointer = metadata_file.tell()

            return parser.parse(item_data, timestamp)

    @classmethod
    def compatible_sensors(cls):
        return [PhotoMetadata, GPS, Acceleration, Compass, OBD, Pressure, Attitude,
                Gravity, OSCDevice, DeviceMotion, CameraParameters, ExifParameters]

    def items(self) -> List[SensorItem]:
        """this method returns all metadata items found in the current metadata file"""
        with self._storage.open(self.file_path) as metadata_file:
            metadata_file.seek(self._body_pointer)
            item_instances = []
            for line in metadata_file:
                timestamp, alias, item_data = self._timestamp_alias_data_from_row(line)
                definition = self._alias_definitions[alias]
                row_parser = definition.parsers[0]
                item_instance = row_parser.parse(item_data, timestamp)
                item_instances.append(item_instance)
            return item_instances

    def serialize(self):
        raise NotImplementedError("MetadataParser serialize method is not implemented", self)

    # <editor-fold desc="Private methods">

    def _configure_headers(self):
        with self._storage.open(self.file_path) as metadata_file:
            self.header_line = metadata_file.readline()
            line = metadata_file.readline()
            if "HEADER" not in line:
                return

            # find the definition lines
            line = metadata_file.readline()
            while line and "BODY" not in line:
                if "ALIAS:" not in line:
                    return
                alias_line_elements = line.split(":")
                if ";" not in alias_line_elements[1]:
                    return

                definition = SensorItemDefinition.definition_from_row(line)
                self._alias_definitions[definition.alias] = definition
                line = metadata_file.readline()

            self._body_pointer = metadata_file.tell()
            self.start_new_reading()

    def _compatible_definition(self, item_class) -> Optional[SensorItemDefinition]:
        """This function returns a compatible definition"""
        for definition in self._alias_definitions.values():
            if definition.parsers:
                parser: ItemParser = definition.parsers[0]
                if parser.item_class == item_class:
                    return definition
        return None

    @classmethod
    def _timestamp_alias_data_from_row(cls, row) -> Optional[Tuple[str, str, str]]:
        if ":" not in row:
            return None
        elements = row.split(":")
        if len(elements) != 3:
            return None
        timestamp = elements[0]
        item_alias = elements[1]
        item_data = elements[2]

        return timestamp, item_alias, item_data

    # </editor-fold>


class MetadataParserLegacy(MetadataParser):
    """this class is a MetadataParser that can parse metadata 1.x versions"""

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        if item_class == OSCDevice:
            return self._device_item

        item = None
        with self._storage.open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            line = metadata_file.readline()
            while line:
                if ";" not in line:
                    line = metadata_file.readline()
                    continue

                elements = line.replace("\n", "").split(";")

                tmp_item = self._get_metadata_item(elements)
                if isinstance(tmp_item, item_class):
                    item = tmp_item
                    break
                line = metadata_file.readline()
            self._data_pointer = metadata_file.tell()

        if item_class == PhotoMetadata and item:
            all_photos_data = self._all_with_classes([GPS, OBD, Compass])
            all_photos_data.append(item)
            all_photos_data.sort(key=lambda i: i.timestamp)
            self._aggregate_photo_data(all_photos_data, 1)
        return item

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        if item_class == PhotoMetadata:
            photo_data_items = self._all_with_classes([PhotoMetadata, GPS, OBD, Compass])
            return self._aggregate_photo_data(photo_data_items)
        if item_class == OSCDevice:
            device = self._device_item
            return [] if device is None else [device]
        return self._all_with_classes([item_class])

    def next_item(self):
        with self._storage.open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            line = metadata_file.readline()
            if ";" not in line:
                return None
            elements = line.replace("\n", "").split(";")
            item = self._get_metadata_item(elements)
            self._data_pointer = metadata_file.tell()

        if isinstance(item, PhotoMetadata) and item:
            all_photos_data = self._all_with_classes([GPS, OBD, Compass])
            all_photos_data.append(item)
            all_photos_data.sort(key=lambda i: i.timestamp)
            self._aggregate_photo_data(all_photos_data, 1)
        return item

    def items(self) -> List[SensorItem]:
        all_items = self._all_with_classes([PhotoMetadata,
                                            DeviceMotion,
                                            Acceleration,
                                            Gravity,
                                            Attitude,
                                            GPS,
                                            OBD,
                                            Pressure,
                                            Compass])

        all_items.sort(key=lambda i: i.timestamp)
        self._aggregate_photo_data(all_items)
        return all_items

    @classmethod
    def compatible_sensors(cls):
        return [PhotoMetadata, GPS, Acceleration, Compass, OBD, Pressure, Attitude,
                Gravity, OSCDevice, DeviceMotion]

    def format_version(self) -> Optional[str]:
        """According to the documentation the version can have on this line as separator a space
        or a comma"""
        if self._metadata_version:
            return self._metadata_version
        self._read_device_attributes()
        return self._metadata_version

    def serialize(self):
        raise NotImplementedError("MetadataParser serialize method is not implemented", self)

    # <editor-fold desc="Private Methods">
    def _configure_headers(self):
        self._metadata_version = None
        self._metadata_legacy_format = self._known_formats()[self.format_version()]
        self._data_pointer = self._body_pointer

    @classmethod
    def _aggregate_photo_data(cls, photo_data_items, limit=-1) -> List[PhotoMetadata]:
        photo_data_items.sort(key=lambda i: i.timestamp)
        previous_gps = None
        previous_obd = None
        previous_compass = None
        photos: List[PhotoMetadata] = []
        for item in photo_data_items:
            if isinstance(item, PhotoMetadata) and previous_gps:
                item.gps = previous_gps
                item.obd = previous_obd
                item.compass = previous_compass
                photos.append(item)
            elif isinstance(item, GPS):
                previous_gps = item
            elif isinstance(item, OBD):
                previous_obd = item
            elif isinstance(item, Compass):
                previous_compass = item
            if limit == len(photos):
                return photos
        return photos

    def _all_with_classes(self, item_classes, file_pointer=-1) -> List[SensorItem]:
        if file_pointer == -1:
            file_pointer = self._body_pointer
        with self._storage.open(self.file_path) as metadata_file:
            metadata_file.seek(file_pointer)
            item_instances = []
            parsers: List[ItemLegacyParser] = []
            for item_class in item_classes:
                parsers.append(self._parser_for_class(item_class))
            for line in metadata_file:
                if ";" not in line:
                    continue
                elements = line.replace("\n", "").split(";")
                tmp_item = None
                for parser in parsers:
                    tmp_item = parser.parse(elements)
                    if tmp_item:
                        break
                if tmp_item:
                    item_instances.append(tmp_item)
            return item_instances

    def _read_device_attributes(self):
        with self._storage.open(self.file_path) as metadata_file:
            header_line = metadata_file.readline()
            self._body_pointer = metadata_file.tell()
            if ";" in header_line:
                elements = header_line.strip().split(";")
                if len(elements) > 6:
                    # to many elements
                    return
                self._device_item = OSCDevice()
                self._device_item.timestamp = "0"
                if len(elements) == 5:
                    # row has the following info:
                    # device_model;os_version;metadata_version;app_version;rec_Type
                    if RecordingType.PHOTO.name.lower() == elements[4]:
                        self._device_item.recording_type = RecordingType.PHOTO
                    elif RecordingType.VIDEO.name.lower() == elements[4]:
                        self._device_item.recording_type = RecordingType.VIDEO

                if len(elements) >= 4:
                    # row has at least the following info:
                    # device_model;os_version;metadata_version;app_version
                    self._device_item.app_version = elements[3]

                if len(elements) >= 3:
                    # row has at least the following info:
                    # device_model;os_version;metadata_version
                    self._device_item.device_raw_name = elements[0]
                    self._device_item.os_version = elements[1]
                    self._metadata_version = elements[2]

            elif " " in header_line:
                elements = header_line.split(" ")
                if len(elements) == 2:
                    self._metadata_version = "no version"
                    self._device_item.device_raw_name = elements[0]
                    self._device_item.recording_type = RecordingType.PHOTO

            if self._device_item.recording_type is None:
                recording_type = self._recording_type_from_version(self._metadata_version)
                self._device_item.recording_type = recording_type

            if "iP" in self._device_item.device_raw_name:
                self._device_item.platform_name = "iOS"
            else:
                self._device_item.platform_name = "Android"

    def _get_metadata_item(self, elements) -> Optional[SensorItem]:
        parsers = [legacy.incomplete_photo_parser(self._metadata_legacy_format),
                   legacy.device_motion_parse(self._metadata_legacy_format),
                   legacy.acceleration_parser(self._metadata_legacy_format),
                   legacy.gravity_parser(self._metadata_legacy_format),
                   legacy.attitude_parser(self._metadata_legacy_format),
                   legacy.gps_parser(self._metadata_legacy_format, self._device_item),
                   legacy.obd_parser(self._metadata_legacy_format),
                   legacy.pressure_parser(self._metadata_legacy_format),
                   legacy.compass_parser(self._metadata_legacy_format)]
        for parser in parsers:
            item = parser.parse(elements)
            if item:
                return item
        return None

    def _parser_for_class(self, item_class):
        class_parser = {PhotoMetadata: legacy.incomplete_photo_parser(self._metadata_legacy_format),
                        DeviceMotion: legacy.device_motion_parse(self._metadata_legacy_format),
                        Acceleration: legacy.acceleration_parser(self._metadata_legacy_format),
                        Gravity: legacy.gravity_parser(self._metadata_legacy_format),
                        Attitude: legacy.attitude_parser(self._metadata_legacy_format),
                        GPS: legacy.gps_parser(self._metadata_legacy_format, self._device_item),
                        OBD: legacy.obd_parser(self._metadata_legacy_format),
                        Pressure: legacy.pressure_parser(self._metadata_legacy_format),
                        Compass: legacy.compass_parser(self._metadata_legacy_format)}
        return class_parser[item_class]

    @classmethod
    def _known_formats(cls):
        return {
            # ts;lon;lat;elv;h_accu;gyroX;gyroY;gyroZ;accX;accY;accZ;pres;mag_X;mag_Y;mag_Z;index
            'no version': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                           'horizontal_accuracy': 4,
                           'gyroscope.x': 5, 'gyroscope.y': 6, 'gyroscope.z': 7,
                           'acceleration.x': 8, 'acceleration.y': 9, 'acceleration.z': 10,
                           'pressure': 11,
                           'magnetic.x': 12, 'magnetic.y': 13, 'magnetic.z': 14,
                           'index': 15},
            # 'ts;lon;lat;elv;h_accu;gyroX;gyroY;gyroZ;accX;accY;accZ;pres;comp;index'
            '1.0.1': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4,
                      'gyroscope.x': 5, 'gyroscope.y': 6, 'gyroscope.z': 7,
                      'acceleration.x': 8, 'acceleration.y': 9, 'acceleration.z': 10,
                      'pressure': 11, 'compass': 12, 'index': 13},
            '1.0.2': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4,
                      'gyroscope.x': 5, 'gyroscope.y': 6, 'gyroscope.z': 7,
                      'acceleration.x': 8, 'acceleration.y': 9, 'acceleration.z': 10,
                      'pressure': 11, 'compass': 12, 'index': 13},
            # ts;lon;lat;elv;h_accu;gyroX;gyroY;gyroZ;accX;accY;accZ;pres;comp;index;gX;gY;gZ
            '1.0.3': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4,
                      'gyroscope.x': 5, 'gyroscope.y': 6, 'gyroscope.z': 7,
                      'acceleration.x': 8, 'acceleration.y': 9, 'acceleration.z': 10,
                      'pressure': 11, 'compass': 12, 'index': 13,
                      'gravity.x': 14, 'gravity.y': 15, 'gravity.z': 16},
            # ts;lon;lat;elv;h_accu;yaw;pitch;roll;accX;accY;accZ;pres;comp;index;gX;gY;gZ
            '1.0.4': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4,
                      'yaw': 5, 'pitch': 6, 'roll': 7,
                      'acceleration.x': 8, 'acceleration.y': 9, 'acceleration.z': 10,
                      'pressure': 11, 'compass': 12, 'index': 13,
                      'gravity.x': 14, 'gravity.y': 15, 'gravity.z': 16},
            # ts;lon;lat;elv;h_accu;GPSs;yaw;pitch;roll;accX;accY;accZ;pres;comp;index;gX;gY;gZ
            '1.0.5': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13, 'index': 14,
                      'gravity.x': 15, 'gravity.y': 16, 'gravity.z': 17},
            # ts;lon;lat;elv;h_accu;GPSs;yaw;pitch;roll;accX;accY;accZ;pres;comp;index;gX;gY;gZ;OBDs
            '1.0.6': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13, 'index': 14,
                      'gravity.x': 15, 'gravity.y': 16, 'gravity.z': 17,
                      'OBDs': 18},
            '1.0.7': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13, 'index': 14,
                      'gravity.x': 15, 'gravity.y': 16, 'gravity.z': 17,
                      'OBDs': 18},
            '1.0.8': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13, 'index': 14,
                      'gravity.x': 15, 'gravity.y': 16, 'gravity.z': 17,
                      'OBDs': 18},
            # video
            # ts;lon;lat;elv;h_accu;GPSs;yaw;pitch;roll;accX;accY;accZ;pres;comp;vIndex;tFIndex;
            # gX;gY;gZ;OBDs
            '1.1': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                    'horizontal_accuracy': 4, 'gps.speed': 5,
                    'yaw': 6, 'pitch': 7, 'roll': 8,
                    'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                    'pressure': 12, 'compass': 13,
                    'video_index': 14, 'frame_index': 15,
                    'gravity.x': 16, 'gravity.y': 17, 'gravity.z': 18,
                    'OBDs': 19},
            '1.1.1': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13,
                      'video_index': 14, 'frame_index': 15,
                      'gravity.x': 16, 'gravity.y': 17, 'gravity.z': 18,
                      'OBDs': 19},
            '1.1.2': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13,
                      'video_index': 14, 'frame_index': 15,
                      'gravity.x': 16, 'gravity.y': 17, 'gravity.z': 18,
                      'OBDs': 19},
            '1.1.3': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13,
                      'video_index': 14, 'frame_index': 15,
                      'gravity.x': 16, 'gravity.y': 17, 'gravity.z': 18,
                      'OBDs': 19},
            '1.1.4': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13,
                      'video_index': 14, 'frame_index': 15,
                      'gravity.x': 16, 'gravity.y': 17, 'gravity.z': 18,
                      'OBDs': 19},
            # ts;lon;lat;elv;h_accu;GPSs;yaw;pitch;roll;accX;accY;accZ;pres;comp;vIndex;tFIndex;
            # gX;gY;gZ;OBDs;v_accu
            '1.1.5': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13,
                      'video_index': 14, 'frame_index': 15,
                      'gravity.x': 16, 'gravity.y': 17, 'gravity.z': 18,
                      'OBDs': 19, 'vertical_accuracy': 20},
            '1.1.6': {'time': 0, 'longitude': 1, 'latitude': 2, 'altitude': 3,
                      'horizontal_accuracy': 4, 'gps.speed': 5,
                      'yaw': 6, 'pitch': 7, 'roll': 8,
                      'acceleration.x': 9, 'acceleration.y': 10, 'acceleration.z': 11,
                      'pressure': 12, 'compass': 13,
                      'video_index': 14, 'frame_index': 15,
                      'gravity.x': 16, 'gravity.y': 17, 'gravity.z': 18,
                      'OBDs': 19, 'vertical_accuracy': 20}
        }

    @classmethod
    def _recording_type_from_version(cls, version) -> Optional[RecordingType]:
        format_recording_type = {
            'no version': RecordingType.PHOTO,
            '1.0.1': RecordingType.PHOTO,
            '1.0.2': RecordingType.PHOTO,
            '1.0.3': RecordingType.PHOTO,
            '1.0.4': RecordingType.PHOTO,
            '1.0.5': RecordingType.PHOTO,
            '1.0.6': RecordingType.PHOTO,
            '1.0.7': RecordingType.PHOTO,
            '1.0.8': RecordingType.PHOTO,
            '1.1': RecordingType.VIDEO,
            '1.1.1': RecordingType.VIDEO,
            '1.1.2': RecordingType.VIDEO,
            '1.1.3': RecordingType.VIDEO,
            '1.1.4': RecordingType.VIDEO,
            '1.1.5': RecordingType.VIDEO,
        }
        if version in format_recording_type:
            return format_recording_type[version]
        return None

    # </editor-fold>


def metadata_parser(file_path, storage: Storage) -> MetadataParser:
    """this method will return a valid metadata parser"""
    with storage.open(file_path) as metadata_file:
        header_line = metadata_file.readline()
        if "METADATA:2.0" in header_line:
            # parse this file with MetadataV2 parser
            return MetadataParser(file_path, storage)
        # fallback on MetadataParserLegacy
        return MetadataParserLegacy(file_path, storage)
