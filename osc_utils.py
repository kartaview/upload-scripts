"""custom upload to support upload progress"""
import os
import gzip
import shutil
import exif_processing
from metadata_manager import MetadataManager
from osc_models import Photo
from metadata_parser import Photo as MetadataPhoto
import constants


def create_exif_from_metadata(path: str):
    """this method will generate exif data from metadata"""
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
        elif ".txt" in file_extension and "metadata" in file_name:
            metadata_file = file_path
            parser = MetadataManager.get_metadata_parser(path + "/" + metadata_file)
            parser.start_new_reading()
            metadata_photos = parser.all_photos()
            metadata_device = parser.device_name()

    if metadata_photos:
        photos.sort(key=lambda x: int(os.path.splitext(os.path.basename(x.path))[0]))
        metadata_photos.sort(key=lambda x: x.frame_index)

    for photo in photos:
        metadata_photo: MetadataPhoto = None
        for tmp_photo in metadata_photos:
            if int(tmp_photo.frame_index) == photo.index:
                metadata_photo = tmp_photo
                break
        if not metadata_photo:
            continue
        __metadata_photo_to_photo(metadata_photo, photo, metadata_device)

    for photo in photos:
        tags = exif_processing.create_required_gps_tags(photo.gps_timestamp,
                                                        photo.latitude,
                                                        photo.longitude)
        exif_processing.add_optional_gps_tags(tags,
                                              photo.gps_speed,
                                              photo.gps_altitude,
                                              photo.gps_compass)
        exif_processing.add_gps_tags(photo.path, tags)


def __metadata_photo_to_photo(metadata_photo: MetadataPhoto, photo: Photo, metadata_device: str):
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
    if metadata_photo.timestamp:
        photo.gps_timestamp = float(metadata_photo.timestamp)


def unzip_metadata(path: str) -> str:
    """Method to unzip the metadata file"""
    with gzip.open(os.path.join(path, constants.METADATA_ZIP_NAME), 'rb') as f_in:
        unzip_path = os.path.join(path, constants.METADATA_NAME)
        with open(unzip_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            return unzip_path
