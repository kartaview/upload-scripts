#!/usr/bin/env python3
"""This script is used to discover video files, or photo files"""

import os
import logging
from typing import Optional, Tuple, List, cast

import constants

from io_storage.storage import Local
from parsers.osc_metadata.parser import metadata_parser
from parsers.exif import ExifParser
from parsers.xmp import XMPParser
from osc_models import VisualData, Photo, Video
from common.models import PhotoMetadata, CameraParameters


LOGGER = logging.getLogger('osc_tools.visual_data_discoverer')


class VisualDataDiscoverer:
    """This class is a abstract discoverer of visual data files"""

    @classmethod
    def discover(cls, path: str) -> Tuple[List[VisualData], str]:
        """This method will discover visual data and will return paths and type"""

    @classmethod
    def discover_using_type(cls, path: str, osc_type: str):
        """this method is discovering the online visual data knowing the type"""


class PhotoDiscovery(VisualDataDiscoverer):
    """This class will discover all photo files"""

    @classmethod
    def discover(cls, path: str) -> Tuple[List[VisualData], str]:
        """This method will discover photos"""
        LOGGER.debug("searching for photos %s", path)
        if not os.path.isdir(path):
            return [], "photo"

        files = os.listdir(path)
        photos = []
        for file_path in files:
            file_name, file_extension = os.path.splitext(file_path)
            if ("jpg" in file_extension.lower() or "jpeg" in file_extension.lower()) and \
                    "thumb" not in file_name.lower():
                LOGGER.debug("found a photo: %s", file_path)
                photo = cls._photo_from_path(os.path.join(path, file_path))
                if photo:
                    photos.append(photo)
        # Sort photo list
        cls._sort_photo_list(photos)
        # Add index to the photo objects
        index = 0
        for photo in photos:
            photo.index = index
            index += 1

        return cast(List[VisualData], photos), "photo"

    @classmethod
    def _photo_from_path(cls, path) -> Optional[Photo]:
        photo = Photo(path)
        return photo

    @classmethod
    def _sort_photo_list(cls, photos):
        photos.sort(key=lambda p: int("".join(filter(str.isdigit, os.path.basename(p.path)))))


class ExifPhotoDiscoverer(PhotoDiscovery):
    """This class will discover all photo files having exif data"""

    @classmethod
    def _photo_from_path(cls, path) -> Optional[Photo]:
        photo = Photo(path)
        exif_parser = ExifParser(path, Local())
        photo_metadata: PhotoMetadata = cast(PhotoMetadata,
                                             exif_parser.next_item_with_class(PhotoMetadata))

        if photo_metadata is None:
            return None

        # required gps timestamp or exif timestamp
        photo.gps_timestamp = photo_metadata.gps.timestamp
        photo.exif_timestamp = photo_metadata.timestamp
        if not photo.gps_timestamp and photo.exif_timestamp:
            photo.gps_timestamp = photo.exif_timestamp

        # required latitude and longitude
        photo.latitude = photo_metadata.gps.latitude
        photo.longitude = photo_metadata.gps.longitude
        if not photo.latitude or \
                not photo.longitude or \
                not photo.gps_timestamp:
            return None

        # optional data
        photo.gps_speed = photo_metadata.gps.speed
        photo.gps_altitude = photo_metadata.gps.altitude
        photo.gps_compass = photo_metadata.compass.compass

        # pylint: disable=W0703
        try:
            xmp_parser = XMPParser(path, Local())
            params: CameraParameters = cast(CameraParameters,
                                            xmp_parser.next_item_with_class(CameraParameters))
            if params is not None:
                photo.fov = params.h_fov
                photo.projection = params.projection
        except Exception:
            pass

        LOGGER.debug("lat/lon: %f/%f", photo.latitude, photo.longitude)
        return photo

    @classmethod
    def _sort_photo_list(cls, photos):
        photos.sort(key=lambda p: (p.gps_timestamp, os.path.basename(p.path)))


class PhotoMetadataDiscoverer(PhotoDiscovery):

    @classmethod
    def discover(cls, path: str):
        photos, visual_type = super().discover(path)
        metadata_file = os.path.join(path, constants.METADATA_NAME)
        if os.path.exists(metadata_file):
            parser = metadata_parser(metadata_file, Local())
            parser.start_new_reading()
            metadata_photos = cast(List[PhotoMetadata], parser.items_with_class(PhotoMetadata))
            remove_photos = []
            for photo in photos:
                if not isinstance(photo, Photo):
                    continue
                for tmp_photo in metadata_photos:
                    if int(tmp_photo.frame_index) == photo.index:
                        metadata_photo_to_photo(tmp_photo, photo)
                        break
                if not photo.latitude or not photo.longitude or not photo.gps_timestamp:
                    remove_photos.append(photo)
            return [x for x in photos if x not in remove_photos], visual_type
        return [], visual_type


def metadata_photo_to_photo(metadata_photo: PhotoMetadata, photo: Photo):
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


class VideoDiscoverer(VisualDataDiscoverer):
    """This class will discover any sequence having a list of videos"""

    @classmethod
    def discover(cls, path: str) -> Tuple[List[VisualData], str]:
        if not os.path.isdir(path):
            return [], "video"

        files = os.listdir(path)
        videos = []

        for file_path in files:
            _, file_extension = os.path.splitext(file_path)
            if "mp4" in file_extension:
                video = Video(os.path.join(path, file_path))
                videos.append(video)
        cls._sort_list(videos)
        index = 0
        for video in videos:
            video.index = index
            index += 1

        return videos, "video"

    @classmethod
    def _sort_list(cls, videos):
        videos.sort(key=lambda v: int("".join(filter(str.isdigit, os.path.basename(v.path)))))
