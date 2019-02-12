"""This module contains the parser for metadata format v1 """
from metadata_parser import MetadataParser
from metadata_parser import Device
from metadata_parser import Photo
from metadata_parser import GPS
from metadata_parser import Acceleration
from metadata_parser import Gravity
from metadata_parser import DeviceMotion
from metadata_parser import Compass
from metadata_parser import Pressure
from metadata_parser import OBD
from metadata_parser import Attitude
from metadata_parser import MetadataItem


class MetadataParserLegacy(MetadataParser):
    """MetadataParserLegacy is a MetadataParser that is capable of parsing metadata format V1"""
    def __init__(self, file_path: str):
        self._metadata_legacy_format = None
        super().__init__(file_path)

    def all_photos(self):
        item_class = Photo
        attributes_classes = {GPS: "gps", OBD: "obd", Compass: "compass"}
        with open(self.file_path) as metadata_file:
            metadata_file.seek(self._body_pointer)
            item_instances = []
            tmp_attributes: {str, str} = {}
            for line in metadata_file:
                if ";" not in line:
                    continue
                elements = line.replace("\n", "").split(";")
                tmp_item = self._get_metadata_item(elements)
                if tmp_item.item_name == item_class.item_name:
                    for property_name, value in tmp_attributes.items():
                        setattr(tmp_item, property_name, value)
                    item_instances.append(tmp_item)
                else:
                    for class_type, class_property in attributes_classes.items():
                        if isinstance(tmp_item, class_type):
                            tmp_attributes[class_property] = tmp_item

            return item_instances

    def metadata_version(self) -> str:
        """According to the documentation the version can have on this line as separator a space
        or a comma"""
        if self._metadata_version:
            return self._metadata_version
        self._read_device_attributes()

        return self._metadata_version

    def device_name(self) -> str:
        if self._device_item:
            return self._device_item.device_raw_name
        self._read_device_attributes()

        return self._device_item.device_raw_name

    def recording_type(self) -> str:
        if self._device_item:
            return self._device_item.recording_type
        self._read_device_attributes()

        return self._device_item.recording_type

    def os_version(self) -> str:
        if self._device_item:
            return self._device_item.os_version
        self._read_device_attributes()

        return self._device_item.os_version

    def next_metadata_item(self):
        with open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            line = metadata_file.readline()
            if ";" not in line:
                return None
            elements = line.replace("\n", "").split(";")
            item = self._get_metadata_item(elements)
            self._data_pointer = metadata_file.tell()

            return item

    def next_item_with_class(self, item_class):
        item = None
        with open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            line = metadata_file.readline()
            while line:
                if ";" not in line:
                    line = metadata_file.readline()
                    continue

                elements = line.replace("\n", "").split(";")

                tmp_item = self._get_metadata_item(elements)
                if tmp_item.item_name == item_class.item_name:
                    item = tmp_item
                    break
                line = metadata_file.readline()
            self._data_pointer = metadata_file.tell()
        return item

    # <editor-fold desc="Private">
    def _configure_headers(self):
        self._metadata_legacy_format = self._known_formats()[self.metadata_version()]
        self._data_pointer = self._body_pointer

    def _read_device_attributes(self):
        with open(self.file_path) as metadata_file:
            header_line = metadata_file.readline()
            self._body_pointer = metadata_file.tell()
            if ";" in header_line:
                elements = header_line.split(";")
                if len(elements) > 6:
                    # to many elements
                    return
                self._device_item = Device()
                if len(elements) == 5:
                    # row has the following info:
                    # device_model;os_version;metadata_version;app_version;rec_Type
                    self._device_item.recording_type = elements[4]

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
                    self._device_item.recording_type = "photo"

            if not self._device_item.recording_type:
                recording_type = self._recording_type_from_version(self._metadata_version)
                self._device_item.recording_type = recording_type

            if "iP" in self._device_item.device_raw_name:
                self._device_item.platform_name = "iOS"
            else:
                self._device_item.platform_name = "Android"

    def _value(self, elements, key):
        if key not in self._metadata_legacy_format:
            return None

        if elements[self._metadata_legacy_format[key]] != '':
            return elements[self._metadata_legacy_format[key]]
        return None

    def _get_item_with_acceleration(self, elements):
        acceleration = self._get_acceleration_item(elements)
        gravity = self._get_gravity_item(elements)
        attitude = self._get_attitude_item(elements)
        if acceleration and gravity and attitude:
            device_motion = DeviceMotion()
            device_motion.gravity = gravity
            device_motion.acceleration = acceleration
            device_motion.gyroscope = attitude
            return device_motion
        if acceleration:
            return acceleration
        if gravity:
            return gravity
        if attitude:
            return attitude
        return None

    def _get_item_with_speed(self, elements):
        gps = self._get_gps_item(elements)
        if gps:
            return gps

        obd = self._get_obd_item(elements)
        if obd:
            return obd
        return None

    def _get_metadata_item(self, elements):
        photo = self._get_photo_item(elements)
        if photo:
            return photo

        item_with_acceleration = self._get_item_with_acceleration(elements)
        if item_with_acceleration:
            return item_with_acceleration

        item_with_speed = self._get_item_with_speed(elements)
        if item_with_speed:
            return item_with_speed
        pressure = self._get_pressure_item(elements)
        if pressure:
            return pressure

        compass = self._get_compass_item(elements)
        if compass:
            return compass
        return None

    def _get_photo_item(self, elements):
        index = self._value(elements, 'index')
        video_index = self._value(elements, 'video_index')
        frame_index = self._value(elements, 'frame_index')
        photo = None

        if index:
            photo = Photo()
            photo.timestamp = self._value(elements, 'time')
            photo.frame_index = index
        elif video_index and frame_index:
            photo = Photo()
            photo.timestamp = self._value(elements, 'time')
            photo.frame_index = frame_index
            photo.video_index = video_index

        return photo

    def _get_acceleration_item(self, elements):
        acc_x = self._value(elements, 'acceleration.x')
        acc_y = self._value(elements, 'acceleration.y')
        acc_z = self._value(elements, 'acceleration.z')

        if acc_x and acc_y and acc_z:
            acceleration = Acceleration()
            acceleration.timestamp = self._value(elements, 'time')
            acceleration.acc_x = acc_x
            acceleration.acc_y = acc_y
            acceleration.acc_z = acc_z
            return acceleration

        return None

    def _get_gravity_item(self, elements):
        acc_x = self._value(elements, 'gravity.x')
        acc_y = self._value(elements, 'gravity.y')
        acc_z = self._value(elements, 'gravity.z')

        if acc_x and acc_y and acc_z:
            gravity = Gravity()
            gravity.timestamp = self._value(elements, 'time')
            gravity.acc_x = acc_x
            gravity.acc_y = acc_y
            gravity.acc_z = acc_z
            return gravity

        return None

    def _get_attitude_item(self, elements):
        yaw = self._value(elements, 'yaw')
        pitch = self._value(elements, 'pitch')
        roll = self._value(elements, 'roll')

        if yaw and pitch and roll:
            attitude = Attitude()
            attitude.timestamp = self._value(elements, 'time')
            attitude.yaw = yaw
            attitude.pitch = pitch
            attitude.roll = roll
            return attitude

        return None

    def _get_gps_item(self, elements):
        latitude = self._value(elements, 'latitude')
        if not latitude:
            return None

        longitude = self._value(elements, 'longitude')
        if not longitude:
            return None

        horizontal_accuracy = self._value(elements, 'horizontal_accuracy')
        if not horizontal_accuracy:
            return None

        elevation = self._value(elements, 'elevation')
        vertical_accuracy = self._value(elements, 'vertical_accuracy')
        gps_speed = self._value(elements, 'gps.speed')

        gps = GPS()
        gps.timestamp = self._value(elements, 'time')
        gps.latitude = latitude
        gps.longitude = longitude
        gps.horizontal_accuracy = horizontal_accuracy
        if elevation:
            gps.altitude = elevation
        if vertical_accuracy:
            gps.vertical_accuracy = vertical_accuracy
        if gps_speed:
            if "waylens" in self.device_name():
                gps_speed = str(float(gps_speed) / 3.6)
            gps.speed = gps_speed

        return gps

    def _get_obd_item(self, elements):
        obd_speed = self._value(elements, 'OBDs')
        if obd_speed:
            obd = OBD()
            obd.timestamp = self._value(elements, 'time')
            obd.speed = obd_speed
            return obd

        return None

    def _get_pressure_item(self, elements):
        value = self._value(elements, 'pressure')
        if value:
            pressure = Pressure()
            pressure.timestamp = self._value(elements, 'time')
            pressure.pressure = value
            return pressure

        return None

    def _get_compass_item(self, elements):
        value = self._value(elements, 'compass')
        if value:
            compass = Compass()
            compass.timestamp = self._value(elements, 'time')
            compass.compass = value
            return compass
        return None

    def _items_with_class(self, item_class) -> [MetadataItem]:
        with open(self.file_path) as metadata_file:
            metadata_file.seek(self._body_pointer)
            item_instances = []
            for line in metadata_file:
                if ";" not in line:
                    continue
                elements = line.replace("\n", "").split(";")
                tmp_item = self._get_metadata_item(elements)
                if not tmp_item:
                    continue
                if tmp_item.item_name == item_class.item_name:
                    item_instances.append(tmp_item)
            return item_instances

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
    def _recording_type_from_version(cls, version):
        format_recording_type = {
            'no version' : "photo",
            '1.0.1': "photo",
            '1.0.2': "photo",
            '1.0.3': "photo",
            '1.0.4': "photo",
            '1.0.5': "photo",
            '1.0.6': "photo",
            '1.0.7': "photo",
            '1.0.8': "photo",
            '1.1': "video",
            '1.1.1': "video",
            '1.1.2': "video",
            '1.1.3': "video",
            '1.1.4': "video",
            '1.1.5': "video",
        }
        if version in format_recording_type:
            return format_recording_type[version]
        return None
    # </editor-fold>
