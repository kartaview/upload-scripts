"""This module is made to parse osc metadata file version 2"""


class MetadataItem:
    """This is a model class representing a generic data item found in metadata file"""
    def __init__(self):
        self.timestamp: float = None

    def __eq__(self, other):
        if isinstance(other, MetadataItem):
            return self.timestamp == other.timestamp
        return False

    def __hash__(self):
        return hash(self.timestamp)


class ItemParser:
    """ItemParser is a parser class that can parse a Metadata2.0 row and return a MetadataItem"""
    def __init__(self, version: int, formats: dict, item_class):
        self.version: int = version
        self.format: dict = formats
        self.item_class = item_class

    def __eq__(self, other):
        if isinstance(other, ItemParser):
            return self.version == other.version and \
                   self.format == other.format and \
                   self.item_class == other.item_class
        return False

    def __hash__(self):
        return hash(self.version, self.format, self.item_class)

    def parse(self, row, timestamp) -> MetadataItem:
        """This method will return a complete Metadata Item instance that was found at the row
        received as parameter"""
        _elements = row.replace("\n", "").split(";")
        if len(_elements) != len(self.format):
            return None

        item_instance = self.item_class()
        item_instance.timestamp = timestamp
        for attribute_key, attribute_value in self.format.items():
            if "." in attribute_key:
                sub_attributes = attribute_key.split(".")
                # get the sub item that has the property that needs to be set
                tmp_item = item_instance
                for level in range(len(sub_attributes)-1):
                    tmp_item = getattr(tmp_item, sub_attributes[level])
                setattr(tmp_item,
                        sub_attributes[len(sub_attributes)-1],
                        ItemParser._value(_elements, attribute_value))

            else:
                setattr(item_instance,
                        attribute_key,
                        _elements[attribute_value])

        return item_instance

    @classmethod
    def _value(cls, elements, key) -> str:
        if elements[key] != '':
            return elements[key]
        return None


class MetadataItemDefinition:
    """MetadataItemDefinition is a model class for the Metadata2.0 header rows"""
    def __init__(self):
        self.alias = None
        self.item_name = None
        self.version = None
        self.min_compatible_version = None
        self.parsers: [ItemParser] = None

    def __eq__(self, other):
        if isinstance(other, MetadataItemDefinition):
            return self.alias == other.alias and \
                   self.item_name == other.item_name and \
                   self.version == other.version and \
                   self.min_compatible_version == other.min_compatible_version and \
                   len(self.parsers) == len(other.parsers)
        return False

    def __hash__(self):
        return hash(self.alias,
                    self.item_name,
                    self.version,
                    self.min_compatible_version,
                    len(self.parsers))

    @classmethod
    def definition_from_row(cls, row):
        """This method will return a MetadataItemDefinition compatible with the row sent as
        parameter. If no compatible MetadataItemDefinition is found then it will return None"""
        if ";" not in row or ":" not in row:
            return None
        elements = row.split(":")
        if len(elements) != 2:
            return None
        elements = elements[1].split(";")
        if len(elements) != 4:
            return None
        definition = MetadataItemDefinition()
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


# <editor-fold: desc="Metadata Item Models">


class Photo(MetadataItem):
    """Photo is a MetadataItem that represents a photo row found in Metadata"""
    item_name = "PHOTO"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.gps: GPS = GPS()
        self.obd: OBD = OBD()
        self.compass: Compass = Compass()
        self.video_index = None
        self.frame_index = None

    def __eq__(self, other):
        if isinstance(other, Photo):
            return self.timestamp == other.timestamp and \
                   self.gps.latitude == other.gps.latitude and \
                   self.gps.longitude == other.gps.longitude and \
                   self.video_index == other.video_index and \
                   self.frame_index == other.frame_idnex
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.gps.latitude,
                    self.gps.longitude,
                    self.video_index,
                    self.frame_index)

    @classmethod
    def parser_v1(cls):
        """This is a factory method that returns a item parser for version 1 of the photo row"""
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
                                  Photo)

        return photo_parser


class GPS(MetadataItem):
    """GPS is a MetadataItem model class that can represent all information found in a GPS
    row from Metadata"""
    item_name = "GPS"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.latitude: float = None
        self.longitude: float = None
        self.altitude: float = None
        # in meters
        self.horizontal_accuracy: float = None
        # in meters
        self.vertical_accuracy: float = None
        # in meters
        self.speed: float = None
        # speed is in m/s

    def __eq__(self, other):
        if isinstance(other, GPS):
            return self.timestamp == other.timestamp and \
                   self.latitude == other.latitude and \
                   self.longitude == other.longitude
        return False

    def __hash__(self):
        return hash(self.timestamp, self.latitude, self.longitude)

    @classmethod
    def parser_v1(cls):
        """This is a factory method to get a ItemParser for the version 1 of the GPS found in
        Metadata format"""
        gps_parser = ItemParser(1, {'latitude': 0,
                                    'longitude': 1,
                                    'altitude': 2,
                                    'horizontal_accuracy': 3,
                                    'vertical_accuracy': 4,
                                    'speed': 5},
                                GPS)
        return gps_parser


class Acceleration(MetadataItem):
    """Acceleration is a MetadataItem model representing a acceleration row form Metadata Format"""
    item_name = "ACCELERATION"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.acc_x: float = None
        self.acc_y: float = None
        self.acc_z: float = None

    def __eq__(self, other):
        if isinstance(other, Acceleration):
            return self.timestamp == other.timestamp and \
                   self.acc_x == other.acc_x and \
                   self.acc_y == other.acc_y and \
                   self.acc_z == other.acc_z
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.acc_x,
                    self.acc_y,
                    self.acc_z)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a Acceleration ItemParser for Acceleration row version 1"""
        parser = ItemParser(1, {'acc_x': 0,
                                'acc_y': 1,
                                'acc_z': 2},
                            Acceleration)
        return parser


class Compass(MetadataItem):
    """Compass is a MetadataItem model class that can represent a row from Metadata Format"""
    item_name = "COMPASS"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.compass: float = None

    def __eq__(self, other):
        if isinstance(other, Compass):
            return self.timestamp == other.timestamp and \
                   self.compass == other.compass
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.compass)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a Compass ItemParser for Compass row version 1"""
        parser = ItemParser(1, {'compass': 0}, Compass)
        return parser


class OBD(MetadataItem):
    """OBD is a MetadataItem model class that can represent a row form Metadata Format"""
    item_name = "OBD"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.speed: float = None

    def __eq__(self, other):
        if isinstance(other, OBD):
            return self.timestamp == other.timestamp and \
                   self.speed == other.speed
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.speed)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a OBD ItemParser for OBD row version 1"""
        parser = ItemParser(1, {'speed': 0}, OBD)
        return parser


class Pressure(MetadataItem):
    """Pressure is a MetadataItem model class that can represent a row form Metadata Format"""
    item_name = "PRESSURE"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.pressure: float = None

    def __eq__(self, other):
        if isinstance(other, Pressure):
            return self.timestamp == other.timestamp and \
                   self.pressure == other.pressure
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.pressure)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a Pressure ItemParser for Pressure row version 1"""
        parser = ItemParser(1, {'pressure': 0}, Pressure)
        return parser


class Attitude(MetadataItem):
    """Attitude is a MetadataItem model class that can represent a row form Metadata Format"""
    item_name = "ATTITUDE"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.yaw: float = None
        self.pitch: float = None
        self.roll: float = None

    def __eq__(self, other):
        if isinstance(other, Attitude):
            return self.timestamp == other.timestamp and \
                   self.yaw == other.yaw and \
                   self.pitch == other.pitch and \
                   self.roll == other.roll
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.yaw,
                    self.pitch,
                    self.roll)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a Attitude ItemParser for Attitude row version 1"""
        parser = ItemParser(1, {'yaw': 0,
                                'pitch': 1,
                                'roll': 2},
                            Attitude)
        return parser


class Gravity(Acceleration):
    """Gravity is a MetadataItem model class that can represent a row form Metadata Format"""
    item_name = "GRAVITY"
    definition: MetadataItemDefinition = None

    def __eq__(self, other):
        if isinstance(other, Gravity):
            return self.timestamp == other.timestamp and \
                   self.acc_x == other.acc_x and \
                   self.acc_y == other.acc_y and \
                   self.acc_z == other.acc_z
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.acc_x,
                    self.acc_y,
                    self.acc_z)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a Gravity ItemParser for Gravity row version 1"""
        parser = ItemParser(1, {'acc_x': 0,
                                'acc_y': 1,
                                'acc_z': 2},
                            Gravity)
        return parser


class DeviceMotion(MetadataItem):
    """DeviceMotion is a MetadataItem model class that can represent a row form Metadata Format"""
    item_name = "DEVICEMOTION"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.gyroscope: Attitude = Attitude()
        self.acceleration: Acceleration = Acceleration()
        self.gravity: Gravity = Gravity()

    def __eq__(self, other):
        if isinstance(other, DeviceMotion):
            return self.timestamp == other.timestamp and \
                   self.gyroscope == other.gyroscope and \
                   self.acceleration == other.acceleration and \
                   self.gravity == other.gravity
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.gyroscope,
                    self.acceleration,
                    self.gravity)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a DeviceMotion ItemParser for DeviceMotion row version 1"""
        parser = ItemParser(1, {'gyroscope.yaw': 0,
                                'gyroscope.pitch': 1,
                                'gyroscope.roll': 2,
                                'acceleration.x': 3,
                                'acceleration.y': 4,
                                'acceleration.z': 5,
                                'gravity.x': 6,
                                'gravity.y': 7,
                                'gravity.z': 8},
                            DeviceMotion)
        return parser


class Device(MetadataItem):
    """Device is a MetadataItem model class that can represent a row form Metadata Format"""
    item_name = "DEVICE"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.platform_name = None
        self.os_raw_name = None
        self.os_version = None
        self.device_raw_name = None
        self.app_version = None
        self.app_build_number = None
        self.recording_type = None

    def __eq__(self, other):
        if isinstance(other, Device):
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
        return hash(self.timestamp,
                    self.platform_name,
                    self.os_raw_name,
                    self.os_version,
                    self.device_raw_name,
                    self.app_version,
                    self.app_build_number,
                    self.recording_type)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a Device ItemParser for Device row version 1"""
        parser = ItemParser(1, {'platform_name': 0,
                                'os_raw_name': 1,
                                'os_version': 2,
                                'device_raw_name': 3,
                                'app_version': 4,
                                'app_build_number': 5,
                                'recording_type': 6},
                            Device)
        return parser


class CameraParameters(MetadataItem):
    """CameraParameters is a MetadataItem model class that can represent a row form
    Metadata Format"""
    item_name = "CAMERA"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.v_fov: str = None
        self.v_zf: str = None
        self.aperture: str = None

    def __eq__(self, other):
        if isinstance(other, CameraParameters):
            return self.timestamp == other.timestamp and \
                   self.v_fov == other.v_fov and \
                   self.v_zf == other.v_zf and \
                   self.aperture == other.aperture
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.v_fov,
                    self.v_zf,
                    self.aperture)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a CameraParameters ItemParser for CameraParameters row
        version 1"""
        parser = ItemParser(1, {'v_fov': 0,
                                'v_zf': 1,
                                'aperture': 2},
                            CameraParameters)
        return parser


class ExifParameters(MetadataItem):
    """ExifParameters is a MetadataItem model class that can represent a row form Metadata Format"""
    item_name = "EXIF"
    definition: MetadataItemDefinition = None

    def __init__(self):
        super().__init__()
        self.focal_length: str = None
        self.f_number: str = None

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.timestamp == other.timestamp and \
                   self.focal_length == other.focal_length and \
                   self.f_number == other.f_number
        return False

    def __hash__(self):
        return hash(self.timestamp,
                    self.focal_length,
                    self.f_number)

    @classmethod
    def parser_v1(cls) -> ItemParser:
        """This method is returns a ExifParameters ItemParser for ExifParameters row version 1"""
        parser = ItemParser(1, {'focal_lenght': 0,
                                'f_number': 1},
                            ExifParameters)
        return parser
# </editor-fold>


class MetadataParser:
    """MetadataParser is a class capable of parsing a Metadata File compatible with the
    known MetadataItem versions"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._body_pointer: int = None
        self._data_pointer: int = None
        self._device_item: Device = None
        self._metadata_version = None
        self._alias_definitions: {str: MetadataItemDefinition} = {}
        self._configure_headers()

    def start_new_reading(self):
        """This method sets the reading file pointer to the body section of the metadata"""
        self._data_pointer = self._body_pointer

    def next_item_with_class(self, item_class) -> MetadataItem:
        """this method returns the next metadata item found in the current metadata file"""
        with open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            item = None
            line = metadata_file.readline()
            while line and "END" not in line:
                timestamp, alias, item_data = self._timestamp_alias_data_from_row(line)
                if alias == item_class.definition.alias:
                    definition = self._alias_definitions[alias]
                    item_parser = definition.parsers[0]
                    item = item_parser.parse(item_data, timestamp)
                    break
                line = metadata_file.readline()
            self._data_pointer = metadata_file.tell()
            return item

        return None

    def all_photos(self):
        """this method returns all the photos from the current metadata file"""
        return self._items_with_class(Photo)

    def next_metadata_item(self) -> MetadataItem:
        """Device name is found in Device item"""
        with open(self.file_path) as metadata_file:
            metadata_file.seek(self._data_pointer)
            line = metadata_file.readline()
            timestamp, alias, item_data = self._timestamp_alias_data_from_row(line)
            definition = self._alias_definitions[alias]
            parser = definition.parsers[0]
            self._data_pointer = metadata_file.tell()

            return parser.parse(item_data, timestamp)

        return None

    def metadata_version(self) -> str:
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

    def device_name(self) -> str:
        """Device name is found in Device item """
        if self._device_item:
            return self._device_item.device_raw_name
        device_items = self._items_with_class(Device)
        if device_items:
            self._device_item = device_items[0]

        return self._device_item.device_raw_name

    def recording_type(self) -> str:
        """Recording type is found in Device item """
        if self._device_item:
            return self._device_item.recording_type
        device_items = self._items_with_class(Device)
        if device_items:
            self._device_item = device_items[0]

        return self._device_item.recording_type

    def os_version(self) -> str:
        """OS version is found in Device item """
        if self._device_item:
            return self._device_item.os_version
        device_items = self._items_with_class(Device)
        if device_items:
            self._device_item = device_items[0]

        return self._device_item.os_version

    # <editor-fold desc="Private">
    def _configure_headers(self):
        with open(self.file_path) as metadata_file:
            self.header_line = metadata_file.readline()
            line = metadata_file.readline()
            if "HEADER" not in line:
                return None

            # find the definition lines
            line = metadata_file.readline()
            while line and "BODY" not in line:
                if "ALIAS:" not in line:
                    return None
                alias_line_elements = line.split(":")
                if ";" not in alias_line_elements[1]:
                    return None

                definition = MetadataItemDefinition.definition_from_row(line)
                self._alias_definitions[definition.alias] = definition
                line = metadata_file.readline()

            self._body_pointer = metadata_file.tell()
            self.start_new_reading()

    @classmethod
    def _timestamp_alias_data_from_row(cls, row) -> (str, str, str):
        if ":" not in row:
            return None
        elements = row.split(":")
        if len(elements) != 3:
            return None
        timestamp = elements[0]
        item_alias = elements[1]
        item_data = elements[2]

        return timestamp, item_alias, item_data

    def _items_with_class(self, item_class) -> [MetadataItem]:
        alias = item_class.definition.alias
        with open(self.file_path) as metadata_file:
            metadata_file.seek(self._body_pointer)
            item_instances = []
            for line in metadata_file:
                name = ":" + alias + ":"
                if name in line and item_class.definition.parsers:
                    response = self._timestamp_alias_data_from_row(line)
                    timestamp = response[0]
                    item_data = response[2]
                    parser = item_class.definition.parsers[0]
                    item_instance = parser.parse(item_data, timestamp)
                    item_instances.append(item_instance)
            return item_instances


def _available_parsers() -> [ItemParser]:
    """This function returns all the available item parsers"""
    photo_parser = Photo.parser_v1()
    gps_parser = GPS.parser_v1()
    acceleration_parser = Acceleration.parser_v1()
    compass_parser = Compass.parser_v1()
    obd_parser = OBD.parser_v1()
    pressure_parser = Pressure.parser_v1()
    attitude_parser = Attitude.parser_v1()
    gravity_parser = Gravity.parser_v1()
    device_parser = Device.parser_v1()
    device_motion_pars = DeviceMotion.parser_v1()
    camera_parser = CameraParameters.parser_v1()
    exif_parser = ExifParameters.parser_v1()

    parsers = [photo_parser,
               gps_parser,
               acceleration_parser,
               compass_parser,
               obd_parser,
               pressure_parser,
               attitude_parser,
               gravity_parser,
               device_parser,
               device_motion_pars,
               camera_parser,
               exif_parser]

    return parsers


def _compatible_parser(definition: MetadataItemDefinition) -> [ItemParser]:
    """This function returns all the compatible item parsers for a specific
    MetadataItemDefinition"""
    item_name = definition.item_name
    min_version = definition.min_compatible_version
    compatible = []
    for parser in _available_parsers():
        if parser.version >= int(min_version) and parser.item_class.item_name == item_name:
            compatible.append(parser)
    return compatible
    # </editor-fold>
