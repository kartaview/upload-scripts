"""
Exif generation from custom geojson file. Required a geojson file containing a
FeatureCollection. Each Feature from the FeatureCollection must contain the folowing properties:
{
    "Timestamp": "%Y-%m-%dT%H:%M:%SZ"
    "Lat": float
    "Lng": float
    "order": int
    "path": image path relative to the geojson file
}
"""
import logging
import os
from typing import List

from parsers.custom_data_parsers.custom_geojson import FeaturePhotoGeoJsonParser, PhotoGeoJson
from parsers.exif import create_required_gps_tags, add_optional_gps_tags, add_gps_tags
from exif_data_generators.exif_generator_interface import ExifGenerator
from io_storage.storage import Local

logger = logging.getLogger(__name__)


class ExifCustomGeoJson(ExifGenerator):

    @staticmethod
    def create_exif(path: str) -> bool:
        logger.warning("Creating exif from custom geojson file %s", path)
        for folder_path, _, files in os.walk(path):
            for file in files:
                _, file_extension = os.path.splitext(file)
                if 'geojson' in file_extension:
                    parser = FeaturePhotoGeoJsonParser(os.path.join(folder_path, file), Local())
                    parser.start_new_reading()
                    custom_photos: List[PhotoGeoJson] = parser.items_with_class(PhotoGeoJson)
                    for photo in custom_photos:
                        absolute_path = os.path.join(folder_path, photo.relative_image_path)
                        if photo.gps.latitude and photo.gps.longitude:
                            tags = create_required_gps_tags(photo.gps.timestamp,
                                                            photo.gps.latitude,
                                                            photo.gps.longitude)
                            add_optional_gps_tags(tags,
                                                  photo.gps.speed,
                                                  photo.gps.altitude,
                                                  photo.compass.compass)
                            add_gps_tags(absolute_path, tags)
        return True

    @staticmethod
    def has_necessary_data(path) -> bool:
        for _, _, files in os.walk(path):
            for file in files:
                _, file_extension = os.path.splitext(file)
                if 'geojson' in file_extension:
                    return True
        return False
