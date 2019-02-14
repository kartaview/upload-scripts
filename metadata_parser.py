"""This module is made to parse osc metadata file version 2"""
from metadata_models import *


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

    # </editor-fold>
