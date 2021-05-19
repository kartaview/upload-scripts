"""utils module that contains useful functions"""
import logging
import os
import gzip
import shutil

from io_storage.storage import Local
from parsers.exif import create_required_gps_tags, add_optional_gps_tags, add_gps_tags
from parsers.osc_metadata.parser import MetadataParser
from osc_models import Photo
from common.models import PhotoMetadata
import constants

LOGGER = logging.getLogger('osc_tools.osc_utils')


def create_exif_from_metadata(path: str):
    """this method will generate exif data from metadata"""
    files = os.listdir(path)
    photos = []
    metadata_photos = []

    if not os.path.isfile(os.path.join(path, constants.METADATA_NAME)):
        LOGGER.warning("WARNING: No OSC metadata file found at %s", path)
        return

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
            parser = MetadataParser.valid_parser(path + "/" + metadata_file, Local())
            parser.start_new_reading()
            metadata_photos = parser.items_with_class(PhotoMetadata)

    if metadata_photos:
        photos.sort(key=lambda x: int(os.path.splitext(os.path.basename(x.path))[0]))
        metadata_photos.sort(key=lambda x: x.frame_index)
    else:
        LOGGER.warning("WARNING: NO metadata photos found at %s", path)
        return

    for photo in photos:
        metadata_photo: PhotoMetadata = None
        for tmp_photo in metadata_photos:
            if int(tmp_photo.frame_index) == photo.index:
                metadata_photo = tmp_photo
                break
        if not metadata_photo:
            continue
        __metadata_photo_to_photo(metadata_photo, photo)

    for photo in photos:
        tags = create_required_gps_tags(photo.gps_timestamp,
                                        photo.latitude,
                                        photo.longitude)
        add_optional_gps_tags(tags,
                              photo.gps_speed,
                              photo.gps_altitude,
                              photo.gps_compass)
        add_gps_tags(photo.path, tags)


def __metadata_photo_to_photo(metadata_photo: PhotoMetadata, photo: Photo):
    if metadata_photo.gps.latitude:
        photo.latitude = float(metadata_photo.gps.latitude)
    if metadata_photo.gps.longitude:
        photo.longitude = float(metadata_photo.gps.longitude)
    if metadata_photo.gps.speed:
        photo.gps_speed = round(float(metadata_photo.gps.speed) * 3.6)
    if metadata_photo.gps.altitude:
        photo.gps_altitude = float(metadata_photo.gps.altitude)
    if metadata_photo.frame_index:
        photo.index = int(metadata_photo.frame_index)
    if metadata_photo.gps.timestamp:
        photo.gps_timestamp = float(metadata_photo.gps.timestamp)


def unzip_metadata(path: str) -> str:
    """Method to unzip the metadata file"""
    with gzip.open(os.path.join(path, constants.METADATA_ZIP_NAME), 'rb') as f_in:
        unzip_path = os.path.join(path, constants.METADATA_NAME)
        with open(unzip_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            return unzip_path
