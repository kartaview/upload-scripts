"""utils module that contains useful functions"""
import logging
import os
import gzip
import shutil
from typing import Type, Dict

import constants
from common.models import GPS
from exif_data_generators.custom_geojson_to_exif import ExifCustomGeoJson
from exif_data_generators.exif_generator_interface import ExifGenerator
from exif_data_generators.metadata_to_exif import ExifMetadataGenerator
from io_storage.storage import Local
from parsers.gpx import GPXParser
from parsers.osc_metadata.parser import metadata_parser

LOGGER = logging.getLogger('osc_tools.osc_utils')


def create_exif(path: str, exif_source: str):
    exif_generators: Dict[str, Type[ExifGenerator]] = {"metadata": ExifMetadataGenerator,
                                                       "custom_geojson": ExifCustomGeoJson}
    if exif_generators[exif_source].has_necessary_data(path):
        exif_generators[exif_source].create_exif(path)
        return
    else:
        LOGGER.info("Exif generation is not possible since necessary data was not found")


def convert_metadata_to_gpx(base_path, sequence_path_ids):
    for sequence_path, sequence_id in sequence_path_ids:
        metadata_handle = metadata_parser(os.path.join(sequence_path, "track.txt"),
                                          Local())
        output_handle = GPXParser(os.path.join(base_path,  str(sequence_id) + ".gpx"), Local())
        output_handle.add_items(metadata_handle.items_with_class(GPS))
        output_handle.serialize()


def unzip_metadata(path: str) -> str:
    """Method to unzip the metadata file"""
    with gzip.open(os.path.join(path, constants.METADATA_ZIP_NAME), 'rb') as f_in:
        unzip_path = os.path.join(path, constants.METADATA_NAME)

        with open(unzip_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            return unzip_path
