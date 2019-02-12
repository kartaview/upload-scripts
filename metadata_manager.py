"""This module will manage metadata parsing"""

import logging
from metadata_parser import MetadataParser
from metadata_parser import Photo, GPS
from metadata_parser_legacy import MetadataParserLegacy


LOGGER = logging.getLogger('osc_tools.metadata_manager')


class MetadataManager:
    """This class is a manager that exposes metadata version agnostic interface"""

    @classmethod
    def get_metadata_parser(cls, file_path: str) -> MetadataParser:
        """This method returns a metadata parser compatible with the file at the specified path"""
        with open(file_path) as metadata_file:
            header_line = metadata_file.readline()
            if "METADATA:2.0" in header_line:
                # parse this file with MetadataV2 parser
                return MetadataParser(file_path)
            if ";" not in header_line:
                # parse as no version
                return MetadataParserLegacy(file_path)

            # parse as versions 1.0.1 -> 1.1.8
            return MetadataParserLegacy(file_path)
        return None

    def valid_metadata(self, path) -> bool:
        """This method returns a bool. If True the metadata is consider valid, or False if
        metadata is not valid."""
        LOGGER.debug("        Validating Metadata %s", path)
        parser = self.get_metadata_parser(path)
        photo_item = parser.next_item_with_class(Photo)
        if photo_item:
            return True
        return False

    def first_location(self, path) -> GPS:
        """This method returns the first gps location from a metadata file path specified as input
        parameter"""
        parser = self.get_metadata_parser(path)
        gps_item = parser.next_item_with_class(GPS)
        return gps_item
