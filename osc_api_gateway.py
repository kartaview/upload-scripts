"""This module is used as a gateway to the OSC api."""
import asyncio
import concurrent.futures
import datetime
import hashlib
import os.path
import shutil
import logging
from typing import Tuple, Optional, List

import requests
import constants
import osc_api_config
from osc_api_config import OSCAPISubDomain
from osc_api_models import OSCSequence, OSCPhoto, OSCUser

LOGGER = logging.getLogger('osc_tools.osc_api_gateway')


def _upload_url(env: OSCAPISubDomain, resource: str) -> str:
    return _osc_url(env) + '/' + _version() + '/' + resource + '/'


def _osc_url(env: OSCAPISubDomain) -> str:
    base_url = __protocol() + env.value + __domain()
    return base_url


def __protocol() -> str:
    return osc_api_config.PROTOCOL


def __domain() -> str:
    return osc_api_config.DOMAIN


def _version() -> str:
    return osc_api_config.VERSION


def _website(url: str) -> str:
    return url.replace("-api", "").replace("api.", "")


class OSCApiMethods:
    """This is a factory class that creates API methods based on environment"""

    @classmethod
    def sequence_create(cls, env: OSCAPISubDomain) -> str:
        """this method will return the link to sequence create method"""
        return _osc_url(env) + "/" + _version() + "/sequence/"

    @classmethod
    def sequence_details(cls, env: OSCAPISubDomain) -> str:
        """this method will return the link to the sequence details method"""
        return _osc_url(env) + "/details"

    @classmethod
    def user_sequences(cls, env: OSCAPISubDomain) -> str:
        """this method returns the urls to the list of sequences that
        belong to a user"""
        return _osc_url(env) + "/my-list"

    @classmethod
    def resource(cls, env: OSCAPISubDomain, resource_name: str) -> str:
        """this method returns the url to a resource"""
        return _osc_url(env) + '/' + resource_name

    @classmethod
    def photo_list(cls, env: OSCAPISubDomain) -> str:
        """this method returns photo list URL"""
        return _osc_url(env) + '/' + _version() + '/sequence/photo-list/'

    @classmethod
    def video_upload(cls, env: OSCAPISubDomain) -> str:
        """this method returns video upload URL"""
        return _upload_url(env, 'video')

    @classmethod
    def photo_upload(cls, env: OSCAPISubDomain) -> str:
        """this method returns photo upload URL"""
        return _upload_url(env, 'photo')

    @classmethod
    def login(cls, env: OSCAPISubDomain, provider: str) -> Optional[str]:
        """this method returns login URL"""
        if provider == "google":
            return _osc_url(env) + '/auth/google/client_auth'
        if provider == "facebook":
            return _osc_url(env) + '/auth/facebook/client_auth'
        # default to OSM
        return _osc_url(env) + '/auth/openstreetmap/client_auth'

    @classmethod
    def finish_upload(cls, env: OSCAPISubDomain) -> str:
        """this method returns a finish upload url"""
        return _osc_url(env) + '/' + _version() + '/sequence/finished-uploading/'


class OSCApi:
    """This class is a gateway for the API"""

    def __init__(self, env: OSCAPISubDomain):
        self.environment = env

    @classmethod
    def __upload_response_success(cls, response: requests.Response,
                                  upload_type: str,
                                  index: int,
                                  sequence_id: int) -> bool:
        if response is None:
            return False
        try:
            json_response = response.json()
            if response.status_code != 200:
                if "status" in json_response and \
                        "apiMessage" in json_response["status"] and \
                        "duplicate entry" in json_response["status"]["apiMessage"]:
                    LOGGER.debug("Received duplicate %s index: %d, photo_id %s sequence_id %s",
                                 upload_type,
                                 index,
                                 None,
                                 sequence_id)
                    return True
                LOGGER.debug("Failed to upload %s index: %d response:%s sequence_id %s",
                             upload_type,
                             index,
                             json_response,
                             sequence_id)
                return False

            if ("osv" in json_response and
                    (("photo" in json_response["osv"] and "id" in json_response["osv"]["photo"]) and
                     ("video" in json_response["osv"] and "id" in json_response["osv"]["video"]))):
                return True
        except ValueError:
            return False
        return False

    def _sequence_page(self, user_name, page) -> Tuple[List[OSCSequence], Exception]:
        try:
            parameters = {'ipp': 100,
                          'page': page,
                          'username': user_name}
            login_url = OSCApiMethods.user_sequences(self.environment)
            response = requests.post(url=login_url, data=parameters)
            json_response = response.json()

            sequences = []
            if 'currentPageItems' in json_response:
                items = json_response['currentPageItems']
                for item in items:
                    sequence = OSCSequence.sequence_from_json(item)
                    sequences.append(sequence)

            return sequences, None
        except requests.RequestException as ex:
            return None, ex

    def authorized_user(self, provider: str, token: str, secret: str) -> Tuple[OSCUser, Exception]:
        """This method will get a authorization token for OSC API"""
        try:
            data_access = {'request_token': token,
                           'secret_token': secret
                           }
            login_url = OSCApiMethods.login(self.environment, provider)
            response = requests.post(url=login_url, data=data_access)
            json_response = response.json()

            if 'osv' in json_response:
                osc_data = json_response['osv']
                user = OSCUser()
                missing_field = None
                if 'access_token' in osc_data:
                    user.access_token = osc_data['access_token']
                else:
                    missing_field = "access token"

                if 'id' in osc_data:
                    user.user_id = osc_data['id']
                else:
                    missing_field = "id"

                if 'username' in osc_data:
                    user.name = osc_data['username']
                else:
                    missing_field = "username"

                if 'full_name' in osc_data:
                    user.full_name = osc_data['full_name']
                else:
                    missing_field = "fullname"

                if missing_field is not None:
                    return None, Exception("OSC API bug. OSCUser missing " + missing_field)

            else:
                return None, Exception("OSC API bug. OSCUser missing username")

        except requests.RequestException as ex:
            return None, ex

        return user, None

    def get_photos(self, sequence_id: int) -> Tuple[List[OSCPhoto], Exception]:
        """this method will return a list of photo objects for a sequence id"""
        try:
            parameters = {'sequenceId': sequence_id}
            login_url = OSCApiMethods.photo_list(self.environment)
            response = requests.post(url=login_url, data=parameters)
            json_response = response.json()
            missing_field = None
            if 'osv' not in json_response:
                missing_field = "osv"
            elif 'photos' not in json_response['osv']:
                missing_field = "photos"
            else:
                photos = []
                photos_json = json_response['osv']['photos']
                for photo_json in photos_json:
                    photo = OSCPhoto.photo_from_json(photo_json)
                    photos.append(photo)
                return photos, missing_field
        except requests.RequestException as ex:
            return [], ex
        return [], Exception("OSC API bug. OSCPhoto missing field:" + missing_field)

    def download_all_images(self, photo_list: [OSCPhoto],
                            track_path: str,
                            override=False,
                            workers: int = 10):
        """This method will download all images to a path overriding or not the files at
        that path. By default this method uses 10 parallel workers."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            loop = asyncio.new_event_loop()
            futures = [
                loop.run_in_executor(executor,
                                     self.get_image, photo, track_path, override)
                for photo in photo_list
            ]
            if not futures:
                loop.close()
                return

            loop.run_until_complete(asyncio.gather(*futures))
            loop.close()

    def get_image(self, photo: OSCPhoto, path: str, override=False) -> Optional[Exception]:
        """downloads the image at the path specified"""
        jpg_name = path + '/' + str(photo.sequence_index) + '.jpg'
        if not override and os.path.isfile(jpg_name):
            return None

        try:
            response = requests.get(OSCApiMethods.resource(self.environment,
                                                           photo.image_name),
                                    stream=True)
            if response.status_code == 200:
                with open(jpg_name, 'wb') as file:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file)
        except requests.RequestException as ex:
            return ex
        return None

    def user_sequences(self, user_name: str) -> Tuple[List[OSCSequence], Exception]:
        """get all tracks for a user id """
        LOGGER.debug("getting all sequences for user: %s", user_name)
        try:
            parameters = {'ipp': 100,
                          'page': 1,
                          'username': user_name}
            json_response = requests.post(url=OSCApiMethods.user_sequences(self.environment),
                                          data=parameters).json()

            if 'totalFilteredItems' not in json_response:
                return [], Exception("OSC API bug missing totalFilteredItems from response")

            total_items = int(json_response['totalFilteredItems'][0])
            pages_count = int(total_items / parameters['ipp']) + 1
            LOGGER.debug("all sequences count: %s pages count: %s",
                         str(total_items), str(pages_count))
            sequences = []
            if 'currentPageItems' in json_response:
                for item in json_response['currentPageItems']:
                    sequences.append(OSCSequence.sequence_from_json(item))

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                loop = asyncio.new_event_loop()
                futures = [
                    loop.run_in_executor(executor,
                                         self._sequence_page, user_name, page)
                    for page in range(2, pages_count + 1)
                ]
                if not futures:
                    loop.close()
                    return sequences, None

                done = loop.run_until_complete(asyncio.gather(*futures))
                loop.close()

                for sequence_page_return in done:
                    # sequence_page method will return a tuple the first element
                    # is a list of sequences
                    sequences = sequences + sequence_page_return[0]

                return sequences, None
        except requests.RequestException as ex:
            return None, ex

    def sequence_link(self, sequence) -> str:
        """This method will return a link to OSC website page displaying the sequence
        sent as parameter"""
        sequence_details_url = OSCApiMethods.sequence_details(self.environment)
        return _website(f"{sequence_details_url}/{str(sequence.online_id)}")

    def download_metadata(self, sequence: OSCSequence, path: str, override=False):
        """this method will download a metadata file of a sequence to the specified path.
        If there is a metadata file at that path by default no override will be made."""
        if sequence.metadata_url is None:
            return None
        metadata_path = path + "/track.txt"
        if not override and os.path.isfile(metadata_path):
            return None

        try:
            response = requests.get(OSCApiMethods.resource(self.environment,
                                                           sequence.metadata_url),
                                    stream=True)
            if response.status_code == 200:
                with open(metadata_path, 'wb') as file:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file)
        except requests.RequestException as ex:
            return ex

        return None

    def create_sequence(self, sequence: OSCSequence, token: str) -> Tuple[int, Exception]:
        """this method will create a online sequence from the current sequence and will return its
        id as a integer or a exception if fail"""
        try:
            parameters = {'uploadSource': 'kv_tools-0.1.0',
                          'access_token': token,
                          'currentCoordinate': sequence.location()
                          }
            if sequence.platform is not None:
                parameters['platformName'] = sequence.platform

            if sequence.device is not None:
                parameters['deviceName'] = sequence.device

            url = OSCApiMethods.sequence_create(self.environment)
            if sequence.metadata_url:
                with open(sequence.metadata_url, 'rb') as metadata_file:
                    load_data = {'metaData': (constants.METADATA_NAME,
                                              metadata_file,
                                              'text/plain')}
                    response = requests.post(url,
                                             data=parameters,
                                             files=load_data)
            else:
                response = requests.post(url, data=parameters)
            json_response = response.json()
            if 'osv' in json_response:
                osc_data = json_response["osv"]
                if "sequence" in osc_data:
                    sequence = OSCSequence.sequence_from_json(osc_data["sequence"])
                    return sequence.online_id, None
        except requests.RequestException as ex:
            return None, ex

        return None, None

    def finish_upload(self, sequence: OSCSequence, token: str) -> Tuple[Optional[bool],
                                                                        Optional[Exception]]:
        """this method must be called in order to signal that a sequence has no more data to be
        uploaded."""
        try:
            parameters = {'sequenceId': sequence.online_id,
                          'access_token': token}
            response = requests.post(OSCApiMethods.finish_upload(self.environment),
                                     data=parameters)
            json_response = response.json()
            if "status" not in json_response:
                # we don't have a proper status documentation
                return False, None
            return True, None
        except requests.RequestException as ex:
            return None, ex

    def upload_video(self, access_token,
                     sequence_id,
                     video_path: str,
                     video_index) -> Tuple[bool, Optional[Exception]]:
        """This method will upload a video to OSC API"""
        try:
            parameters = {'access_token': access_token,
                          'sequenceId': sequence_id,
                          'sequenceIndex': video_index
                          }
            with open(video_path, 'rb') as video_file:
                load_data = {'video': (os.path.basename(video_path),
                                       video_file,
                                       'video/mp4')}
                video_upload_url = OSCApiMethods.video_upload(self.environment)
                response = requests.post(video_upload_url,
                                         data=parameters,
                                         files=load_data,
                                         timeout=100)
            return OSCApi.__upload_response_success(response,
                                                    "video",
                                                    video_index,
                                                    sequence_id), None
        except requests.RequestException as ex:
            LOGGER.debug("Received exception on video upload %s", str(ex))
            return False, ex

    # pylint: disable=R0913,R0914
    def upload_photo(self, access_token,
                     sequence_id,
                     photo: OSCPhoto,
                     photo_path: str,
                     fov=None,
                     projection=None) -> Tuple[bool, Optional[Exception]]:
        """This method will upload a photo to OSC API"""
        LOGGER.debug("uploading photo %s, sequence id %s", photo_path, sequence_id)
        try:
            shot_date = datetime.datetime.utcfromtimestamp(photo.timestamp)
            shot_date_string = shot_date.strftime('%Y-%m-%d %H:%M:%S')
            parameters = {'access_token': access_token,
                          'coordinate': str(photo.latitude) + "," + str(photo.longitude),
                          'sequenceId': sequence_id,
                          'sequenceIndex': photo.sequence_index,
                          'shotDate': shot_date_string
                          }
            if photo.compass:
                parameters["headers"] = photo.compass

            if fov is not None and projection is not None:
                parameters['projection'] = projection
                parameters['fieldOfView'] = fov

            if photo.yaw is not None:
                parameters["projectionYaw"] = photo.yaw

            photo_upload_url = OSCApiMethods.photo_upload(self.environment)
            name = str(hashlib.md5(os.path.basename(photo.image_name).encode()).hexdigest())
            extension = os.path.split(photo.image_name)[1]
            name += extension
            with open(photo_path, 'rb') as image_file:
                load_data = {'photo': (name,
                                       image_file,
                                       'image/jpeg')}
                response = requests.post(photo_upload_url,
                                         data=parameters,
                                         files=load_data,
                                         timeout=100)
            success = self.__upload_response_success(response,
                                                     "photo",
                                                     photo.sequence_index,
                                                     sequence_id)
            return success, None
        except requests.RequestException as ex:
            LOGGER.debug("Received exception on photo upload %s", str(ex))
            return False, ex
    # pylint: enable=R0913,R0914
