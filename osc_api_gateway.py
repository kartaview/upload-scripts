"""This module is used as a gateway to the OSC api."""
import asyncio
import concurrent.futures
import os.path
import shutil
import logging
from enum import Enum
import requests
import constants

LOGGER = logging.getLogger('osc_tools.osc_api_gateway')


def _upload_url(env: str, resource: str) -> str:
    return _osc_url(env) + '/' + _version() + '/' + resource + '/'


def _osc_url(env: str) -> str:
    base_url = __protocol() + env + __domain()
    return base_url


def __protocol() -> str:
    return 'https://'


def __domain() -> str:
    return 'openstreetcam.org'


def _version() -> str:
    return '1.0'


def _website(url: str) -> str:
    return url.replace("-api", "")


class OSCAPIEnvironment(Enum):
    """This is a enumeration of environments"""
    TESTING = 'testing-api.'
    STAGING = 'staging-api.'
    BETA = 'beta-api.'
    PRODUCTION = 'api.'


class OSCApiMethods:
    """This is a factory class that creates API methods based on environment"""

    @classmethod
    def sequence_create(cls, env: str) -> str:
        """this method will return the link to sequence create method"""
        return _osc_url(env) + "/" + _version() + "/sequence/"

    @classmethod
    def sequence_details(cls, env: str) -> str:
        """this method will return the link to the sequence details method"""
        return _osc_url(env) + "/details"

    @classmethod
    def user_sequences(cls, env: str) -> str:
        """this method returns the urls to the list of sequences that
        belong to a user"""
        return _osc_url(env) + "/my-list"

    @classmethod
    def resource(cls, env: str, resource_name: str) -> str:
        """this method returns the url to a resource"""
        return _osc_url(env) + '/' + resource_name

    @classmethod
    def photo_list(cls, env: str) -> str:
        """this method returns photo list URL"""
        return _osc_url(env) + '/' + _version() + '/sequence/photo-list/'

    @classmethod
    def video_upload(cls, env: str) -> str:
        """this method returns video upload URL"""
        return _upload_url(env, 'video')

    @classmethod
    def photo_upload(cls, env: str) -> str:
        """this method returns photo upload URL"""
        return _upload_url(env, 'photo')

    @classmethod
    def login(cls, env: str, provider: str) -> str:
        """this method returns login URL"""
        if provider == "osm":
            return _osc_url(env) + '/auth/openstreetmap/client_auth'
        if provider == "google":
            return _osc_url(env) + '/auth/google/client_auth'
        if provider == "facebook":
            return _osc_url(env) + '/auth/facebook/client_auth'
        return None

    @classmethod
    def finish_upload(cls, env: str) -> str:
        """this method returns a finish upload url"""
        return _osc_url(env) + '/' + _version() + '/sequence/finished-uploading/'


class OSCUser:
    """This class is model for OSC User"""

    def __init__(self):
        self.name = ""
        self.user_id = ""
        self.full_name = ""
        self.access_token = ""

    def description(self) -> str:
        """description method that will return a string representation for this class"""
        return "{ name: " + self.name + \
               ", user_id: " + self.user_id + \
               ", full_name: " + self.full_name + \
               ", access_token = " + self.access_token + " }"

    def __eq__(self, other):
        if isinstance(other, OSCUser):
            return self.user_id == other.user_id
        return False

    def __hash__(self):
        return hash(self.user_id)


class OSCPhoto:
    """this is a model class for a photo from OSC API"""

    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.compass = None
        self.sequence_index = None
        self.photo_id = None
        self.image_name = None
        self.date_added = None

    @classmethod
    def photo_from_json(cls, json):
        """factory method to build a photo from a json representation"""
        photo = OSCPhoto()
        if 'lat' in json:
            photo.latitude = json['lat']
        if 'lon' in json:
            photo.longitude = json['lon']
        if 'sequence_index' in json:
            photo.sequence_index = json['sequence_index']
        if 'id' in json:
            photo.photo_id = json['id']
        if 'name' in json:
            photo.image_name = json['name']
        if 'date_added' in json:
            photo.date_added = json['date_added']

        return photo

    def __eq__(self, other):
        if isinstance(other, OSCPhoto):
            return self.photo_id == other.photo_id
        return False

    def __hash__(self):
        return hash(self.photo_id)


class OSCSequence:
    """this is a model class for a sequence from OSC API"""

    def __init__(self):
        self.photos: [OSCPhoto] = []
        self.local_id: str = None
        self.online_id: str = None
        self.path: str = None
        self.metadata_url = None
        self.latitude = None
        self.longitude = None

    @classmethod
    def sequence_from_json(cls, json):
        """factory method to build a sequence form json representation"""
        sequence = OSCSequence()
        if 'id' in json:
            sequence.online_id = json['id']
        if 'meta_data_filename' in json:
            sequence.metadata_url = json['meta_data_filename']
        if 'photos' in json:
            photos = []
            photos_json = json['photos']
            for photo_json in photos_json:
                photo = OSCPhoto.photo_from_json(photo_json)
                photos.append(photo)
            sequence.photos = photos

        return sequence

    def __eq__(self, other):
        if isinstance(other, OSCSequence):
            return self.local_id == other.local_id and self.online_id == other.online_is
        return False

    def __hash__(self):
        return hash(self.local_id, self.online_id)

    def location(self) -> str:
        """this method returns the string representation of a OSCSequence location"""
        if self.photos:
            photo = self.photos[0]
            return str(photo.latitude) + "," + str(photo.longitude)
        return ""


class OSCApi:
    """This class is a gateway for the API"""

    def __init__(self, env: OSCAPIEnvironment):
        self.environment = env

    @classmethod
    def __upload_response_success(cls, response: requests.Response,
                                  upload_type: str,
                                  index: int) -> bool:
        if response is None:
            return False

        if response.status_code != 200:
            json_response = response.json()
            if "status" in json_response and \
                    "apiMessage" in json_response["status"] and \
                    "duplicate entry" in json_response["status"]["apiMessage"]:
                LOGGER.debug("Received duplicate %s index: %d", upload_type, index)
                return True
            LOGGER.debug("Failed to upload %s index: %d", upload_type, index)
            return False
        return True

    def _sequence_page(self, user_name, page) -> ([OSCSequence], Exception):
        try:
            parameters = {'ipp': 100,
                          'page': page,
                          'username': user_name}
            login_url = OSCApiMethods.user_sequences(self.environment.value)
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

    def authorized_user(self, provider: str, token: str, secret: str) -> (OSCUser, Exception):
        """This method will get a authorization token for OSC API"""
        try:
            data_access = {'request_token': token,
                           'secret_token': secret
                           }
            login_url = OSCApiMethods.login(self.environment.value, provider)
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

    def get_photos(self, sequence_id: int) -> ([OSCPhoto], Exception):
        """this method will return a list of photo objects for a sequence id"""
        try:
            parameters = {'sequenceId': sequence_id}
            login_url = OSCApiMethods.photo_list(self.environment.value)
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

    def get_image(self, photo: OSCPhoto, path: str, override=False) -> Exception:
        """downloads the image at the path specified"""
        jpg_name = path + '/' + str(photo.sequence_index) + '.jpg'
        if not override and os.path.isfile(jpg_name):
            return None

        try:
            response = requests.get(OSCApiMethods.resource(self.environment.value,
                                                           photo.image_name),
                                    stream=True)
            if response.status_code == 200:
                with open(jpg_name, 'wb') as file:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file)
        except requests.RequestException as ex:
            return ex

        return None

    def user_sequences(self, user_name: str) -> ([OSCSequence], Exception):
        """get all tracks for a user id """
        LOGGER.debug("getting all sequences for user: %s", user_name)
        try:
            parameters = {'ipp': 100,
                          'page': 1,
                          'username': user_name}
            json_response = requests.post(url=OSCApiMethods.user_sequences(self.environment.value),
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

    def sequence_details(self, sequence_id: str) -> OSCSequence:
        """method that returns the details of a sequence from OSC API"""
        try:
            parameters = {'id': sequence_id
                          }
            response = requests.post(OSCApiMethods.sequence_details(self.environment.value),
                                     data=parameters)
            json_response = response.json()
            if 'osv' in json_response:
                osc_data = json_response['osv']
                sequence = OSCSequence.sequence_from_json(osc_data)
                sequence.online_id = sequence_id
                return sequence
        except requests.RequestException as ex:
            return ex

        return None

    def sequence_link(self, sequence) -> str:
        """This method will return a link to OSC website page displaying the sequence
        sent as parameter"""
        return _website(OSCApiMethods.sequence_details(self.environment.value)) + \
               "/" + str(sequence.online_id)

    def download_metadata(self, sequence: OSCSequence, path: str, override=False):
        """this method will download a metadata file of a sequence to the specified path.
        If there is a metadata file at that path by default no override will be made."""
        if sequence.metadata_url is None:
            return None
        metadata_path = path + "/track.txt"
        if not override and os.path.isfile(metadata_path):
            return None

        try:
            response = requests.get(OSCApiMethods.resource(self.environment.value,
                                                           sequence.metadata_url),
                                    stream=True)
            if response.status_code == 200:
                with open(metadata_path, 'wb') as file:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file)
        except requests.RequestException as ex:
            return ex

        return None

    def create_sequence(self, sequence: OSCSequence, token: str) -> (int, Exception):
        """this method will create a online sequence from the current sequence and will return its
        id as a integer or a exception if fail"""
        try:
            parameters = {'uploadSource': 'Python',
                          'access_token': token,
                          'currentCoordinate': sequence.location()
                          }
            url = OSCApiMethods.sequence_create(self.environment.value)
            if sequence.metadata_url:
                load_data = {'photo': (constants.METADATA_NAME,
                                       open(sequence.metadata_url, 'rb'),
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

    def finish_upload(self, sequence: OSCSequence, token: str) -> (bool, Exception):
        """this method must be called in order to signal that a sequence has no more data to be
        uploaded."""
        try:
            parameters = {'sequenceId': sequence.online_id,
                          'access_token': token}
            response = requests.post(OSCApiMethods.finish_upload(self.environment.value),
                                     data=parameters)
            json_response = response.json()
            if "status" not in json_response:
                # we don't have a proper status documentation
                return False, None
            return True, None
        except requests.RequestException as ex:
            return None, ex

        return None, None

    def upload_video(self, access_token,
                     sequence_id,
                     video_path: str,
                     video_index) -> (bool, Exception):
        """This method will upload a video to OSC API"""
        try:
            parameters = {'access_token': access_token,
                          'sequenceId': sequence_id,
                          'sequenceIndex': video_index
                          }
            load_data = {'video': (video_path, open(video_path, 'rb'), 'video/mp4')}
            video_upload_url = OSCApiMethods.video_upload(self.environment.value)
            response = requests.post(video_upload_url,
                                     data=parameters,
                                     files=load_data,
                                     timeout=100)
            return OSCApi.__upload_response_success(response, "video", video_index), None
        except requests.RequestException as ex:
            LOGGER.debug("Received exception on video upload %s", str(ex))
            return False, ex

    def upload_photo(self, access_token,
                     sequence_id,
                     photo: OSCPhoto,
                     photo_path: str) -> (bool, Exception):
        """This method will upload a photo to OSC API"""
        try:
            parameters = {'access_token': access_token,
                          'coordinate': str(photo.latitude) + "," + str(photo.longitude),
                          'sequenceId': sequence_id,
                          'sequenceIndex': photo.sequence_index
                          }
            if photo.compass:
                parameters["headers"] = photo.compass

            photo_upload_url = OSCApiMethods.photo_upload(self.environment.value)
            load_data = {'photo': (photo.image_name,
                                   open(photo_path, 'rb'),
                                   'image/jpeg')}
            response = requests.post(photo_upload_url,
                                     data=parameters,
                                     files=load_data,
                                     timeout=100)
            return OSCApi.__upload_response_success(response, "photo", photo.sequence_index), None
        except requests.RequestException as ex:
            LOGGER.debug("Received exception on photo upload %s", str(ex))
            return False, ex
