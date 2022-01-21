"""This file contains all the osc api models """
import datetime
from decimal import Decimal
from typing import Optional


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

    # pylint: disable=R0902
    def __init__(self):
        self.timestamp = None
        self.latitude = None
        self.longitude = None
        self.compass = None
        self.sequence_index = None
        self.photo_id = None
        self.image_name = None
        self.date_added = None
        self.status = None
        self.processing_status = None
        self._file_url = None
        self.yaw = None
        self.projection = None
        self.field_of_view = None
    # pylint: enable=R0902

    @classmethod
    def photo_from_json(cls, json):
        """factory method to build a photo from a json representation"""
        shot_date = json.get('shotDate', None)
        if shot_date is None:
            return None
        photo = OSCPhoto()
        photo.photo_id = json.get('id', None)
        photo.latitude = json.get('lat', None)
        photo.longitude = json.get('lng', None)
        photo.timestamp = datetime.datetime.strptime(shot_date, '%Y-%m-%d %H:%M:%S').timestamp()
        photo.sequence_index = json.get('sequenceIndex', None)

        if photo.photo_id is None or \
                photo.latitude is None or \
                photo.longitude is None or \
                photo.sequence_index is None or \
                photo.timestamp is None:
            return None

        photo.photo_id = int(photo.photo_id)
        photo.latitude = float(photo.latitude)
        photo.longitude = float(photo.longitude)
        photo.sequence_index = int(photo.sequence_index)

        photo.date_added = json.get('dateAdded', None)
        photo.status = json.get("status", None)
        photo.processing_status = json.get("autoImgProcessingStatus", None)
        photo._file_url = json.get("fileurl", None)
        photo.field_of_view = int(json.get("fieldOfView")) if json.get("fieldOfView") else None
        photo.projection = json.get("projection", None)
        photo.yaw = json.get("projectionYaw", None)

        return photo

    def photo_url(self):
        return self._proc_url() if self.projection == "PLANE" else self._wrapped_proc_url

    def _wrapped_proc_url(self):
        if self._file_url is None:
            return None
        return self._file_url.replace("{{sizeprefix}}", "wrapped_proc")

    def _proc_url(self):
        if self._file_url is None:
            return None
        return self._file_url.replace("{{sizeprefix}}", "proc")

    def __eq__(self, other):
        if isinstance(other, OSCPhoto):
            return self.photo_id == other.photo_id
        return False

    def __hash__(self):
        return hash(self.photo_id)


class OSCCameraParameters:
    def __init__(self, focal_length, horizontal_fov, vertical_fov,
                 aperture: Optional[Decimal] = None):
        self.focal_length: Decimal = focal_length
        self.horizontal_fov: Decimal = horizontal_fov
        self.vertical_fov: Decimal = vertical_fov
        self.aperture: Optional[Decimal] = aperture

    @classmethod
    def from_json(cls, json):
        if json is None:
            return None
        camera = OSCCameraParameters(
            json["fLen"],
            json["hFoV"],
            json["vFoV"],
            json["aperture"]
        )
        return camera


class OSCSequence:
    """this is a model class for a sequence from OSC API"""

    # pylint: disable=R0902
    def __init__(self):
        self.photos: [OSCPhoto] = []
        self.local_id: Optional[str] = None
        self.online_id: Optional[str] = None
        self.device: Optional[str] = None
        self.platform: Optional[str] = None
        self.path: Optional[str] = None
        self.metadata_url = None
        self.latitude = None
        self.longitude = None
        self.processing_status: Optional[str] = None
        self.status: Optional[str] = None
        self.recording_type: Optional[str] = None
        self.upload_status: Optional[str] = None
        self.processing_list: Optional[list] = None
        self.recording_date: Optional[str] = None
        self.length: Optional[int] = None
        self.app_version: Optional[str] = None
        self.points: Optional[str] = None
        self.total_images: Optional[int] = None
        self.date_added: Optional[str] = None
        self.is_video: Optional[bool] = None
        self.camera_parameters: Optional[OSCCameraParameters] = None

    # pylint: enable=R0902

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

    @classmethod
    def from_json(cls, json):
        sequence = OSCSequence()
        sequence.online_id = json.get('id', None)
        sequence.metadata_url = json.get('metadataFileUrl', None)
        sequence.processing_status = json.get('processingStatus', None)
        sequence.status = json.get('status', None)
        sequence.device = json.get('deviceName', None)
        sequence.platform = json.get('platformName', None)
        sequence.latitude = json.get('currentLat', None)
        sequence.longitude = json.get('currentLng', None)
        sequence.app_version = json.get('app_version', None)
        sequence_date_added = json.get('dateAdded', None)
        sequence.total_images = int(json.get('countActivePhotos')) if bool(json.get(
            'countActivePhotos')) else None
        sequence.is_video = True if json.get('isVideo', None) == "1" else False
        sequence.camera_parameters = OSCCameraParameters.from_json(json["cameraParameters"])
        if sequence_date_added is not None:
            sequence.date_added = datetime.datetime.strptime(sequence_date_added,
                                                             '%Y-%m-%d %H:%M:%S')

        return sequence

    def __eq__(self, other):
        if isinstance(other, OSCSequence):
            return self.local_id == other.local_id and self.online_id == other.online_id
        return False

    def __hash__(self):
        return hash((self.local_id, self.online_id))

    def location(self) -> str:
        """this method returns the string representation of a OSCSequence location"""
        if self.latitude is not None and self.longitude is not None:
            return str(self.latitude) + "," + str(self.longitude)

        if self.photos:
            photo = self.photos[0]
            return str(photo.latitude) + "," + str(photo.longitude)
        return ""
