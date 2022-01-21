"""
This module is created in order to support the download of user uploaded data
"""

import logging
import os

from concurrent.futures import (
    as_completed,
    ThreadPoolExecutor,
)

from typing import List, Tuple

from tqdm import tqdm

from common.models import GPS
from io_storage.storage import Local
from login_controller import LoginController
from osc_api_config import OSCAPISubDomain
from osc_api_gateway import OSCApi
from osc_api_models import OSCPhoto
from parsers.exif import ExifParser

LOGGER = logging.getLogger('osc_tools.osc_utils')


def download_user_images(to_path):
    login_controller = LoginController(OSCAPISubDomain.PRODUCTION)  # production environement
    # login to get the valid user
    user = login_controller.login()
    osc_api = login_controller.osc_api

    # get all the sequneces for this user
    sequences, error = osc_api.user_sequences(user.name)
    if error:
        LOGGER.info("Could not get sequences for the current user, try again or report a issue on "
                    "github")
        return

    user_dir_path = os.path.join(to_path, user.name)
    os.makedirs(user_path, exist_ok=True)

    # download each sequence
    for sequence in tqdm(sequences, desc="Downloading Sequences"):
        if sequence is None or isinstance(sequence, BaseException):
            continue

        sequence_path = os.path.join(user_path, str(sequence.online_id))
        os.makedirs(sequence_path, exist_ok=True)

        download_success, _ = _download_photo_sequence(osc_api,
                                                       sequence,
                                                       sequence_path,
                                                       add_gps_to_exif=True)
        if not download_success:
            LOGGER.info("There was an error downloading the sequence: %s", str(sequence.online_id))
            continue


def _download_photo_sequence(osc_api: OSCApi,
                             sequence,
                             sequence_path: str,
                             add_gps_to_exif: bool = False) -> Tuple[bool, List[OSCPhoto]]:
    photos, error = osc_api.get_photos(sequence.online_id)
    if error:
        return False, []
    # download metadata
    if sequence.metadata_url is not None:
        metadata_path = os.path.join(sequence_path, sequence.online_id + ".txt")
        osc_api.download_resource(sequence.metadata_url, metadata_path, Local())
        sequence.metadata_url = metadata_path

    # download photos
    download_success = True
    download_bar = tqdm(total=len(photos),
                        desc="Downloading from sequence " + str(sequence.online_id))
    with ThreadPoolExecutor(max_workers=10) as executors:
        futures = [executors.submit(_download_photo,
                                    photo,
                                    sequence_path,
                                    osc_api,
                                    add_gps_to_exif) for photo in photos]
        for future in as_completed(futures):
            photo_success, _ = future.result()
            download_success = download_success and photo_success
            download_bar.update(1)
    if not download_success:
        LOGGER.info("Download failed for sequence %s", str(sequence.online_id))
        return False, []
    return True, photos


def _download_photo(photo: OSCPhoto,
                    folder_path: str,
                    osc_api: OSCApi,
                    add_gps_to_exif: bool = False):
    photo_download_name = os.path.join(folder_path, str(photo.sequence_index) + ".jpg")
    local_storage = Local()
    photo_success, error = osc_api.download_resource(photo.photo_url(),
                                                     photo_download_name,
                                                     local_storage)
    if error or not photo_success:
        LOGGER.debug("Failed to download image: %s", photo.photo_url())

    if add_gps_to_exif:
        parser = ExifParser(photo_download_name, local_storage)
        if len(parser.items_with_class(GPS)) == 0:
            item = GPS()
            item.latitude = photo.latitude
            item.longitude = photo.longitude
            item.timestamp = photo.timestamp
            parser.add_items([item])
            parser.serialize()
    return photo_success, error
