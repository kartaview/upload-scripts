"""
This module is used to generate exif data from OSC Metadata file recorded by iOS or Android apps.
"""
import logging
import os
from typing import cast, List

import constants
from common.models import PhotoMetadata
from exif_data_generators.exif_generator_interface import ExifGenerator
from io_storage.storage import Local
from osc_models import Photo
from parsers.exif.utils import create_required_gps_tags, add_optional_gps_tags, add_gps_tags
from parsers.osc_metadata.parser import metadata_parser

logger = logging.getLogger(__name__)


class ExifMetadataGenerator(ExifGenerator):

    @staticmethod
    def create_exif(path: str) -> bool:
        """this method will generate exif data from metadata"""
        logger.warning("Creating exif from metadata file %s", path)
        files = os.listdir(path)
        photos = []
        metadata_photos = []

        for file_path in files:
            file_name, file_extension = os.path.splitext(file_path)
            if ("jpg" in file_extension or "jpeg" in file_extension) \
                    and "thumb" not in file_name.lower():
                photo = Photo(os.path.join(path, file_path))
                if file_name.isdigit():
                    photo.index = int(file_name)
                photos.append(photo)
            elif ".txt" in file_extension and constants.METADATA_NAME in file_path:
                metadata_file = file_path
                parser = metadata_parser(os.path.join(path, metadata_file), Local())
                parser.start_new_reading()
                metadata_photos = cast(List[PhotoMetadata], parser.items_with_class(PhotoMetadata))

        if metadata_photos:
            photos.sort(key=lambda x: int(os.path.splitext(os.path.basename(x.path))[0]))
            metadata_photos.sort(key=lambda x: x.frame_index)
        else:
            logger.warning("WARNING: NO metadata photos found at %s", path)
            return False

        for photo in photos:
            for tmp_photo in metadata_photos:
                metadata_photo: PhotoMetadata = cast(PhotoMetadata, tmp_photo)
                if (int(metadata_photo.frame_index) == photo.index and
                        metadata_photo.gps.latitude and metadata_photo.gps.longitude):
                    tags = create_required_gps_tags(metadata_photo.gps.timestamp,
                                                    metadata_photo.gps.latitude,
                                                    metadata_photo.gps.longitude)
                    add_optional_gps_tags(tags,
                                          metadata_photo.gps.speed,
                                          metadata_photo.gps.altitude,
                                          metadata_photo.compass.compass)
                    add_gps_tags(photo.path, tags)
                    break

        return True

    @staticmethod
    def has_necessary_data(path) -> bool:
        return os.path.isfile(os.path.join(path, constants.METADATA_NAME))
