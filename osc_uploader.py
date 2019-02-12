"""this module will be used to upload files to osc server"""

import logging
import json
import threading
from concurrent.futures import as_completed, ThreadPoolExecutor
# third party
from tqdm import tqdm
# local imports
import constants
from osc_discoverer import Sequence
from visual_data_discover import Photo, Video
from login_controller import LoginController
from osc_api_gateway import OSCPhoto, OSCSequence

LOGGER = logging.getLogger('osc_uploader')
THREAD_LOCK = threading.Lock()


class OSCUploadManager:
    """OSCUploadManager is a manager that is responsible with managing the upload of the
    sequences received as input"""
    def __init__(self, login_controller: LoginController, max_workers: int = 10):
        self.progress_bar: tqdm = None
        self.sequences: [Sequence] = []
        self.visual_data_count = 0
        self.login_controller: LoginController = login_controller
        self.max_workers = max_workers

    def add_sequence_to_upload(self, sequence: Sequence):
        """Method to add a sequence to upload queue"""
        self.sequences.append(sequence)

    def add_sequences_to_upload(self, sequences: [Sequence]):
        """Method to add a list of sequences to the upload queue"""
        self.sequences = self.sequences + sequences

    def start_upload(self):
        """Method to start upload"""
        LOGGER.warning("Starting to upload %d sequences...", len(self.sequences))
        user = self.login_controller.login()
        with THREAD_LOCK:
            total = 0
            for sequence in self.sequences:
                total = total + len(sequence.visual_items)
            self.progress_bar = tqdm(total=total)

        sequence_operation = SequenceUploadOperation(self,
                                                     user.access_token,
                                                     self.max_workers)

        with ThreadPoolExecutor(max_workers=1) as executors:
            futures = [executors.submit(sequence_operation.upload,
                                        sequence) for sequence in self.sequences]
            report = []
            for future in as_completed(futures):
                success, sequence = future.result()
                report.append((success, sequence))
                if success:
                    LOGGER.warning("    Uploaded sequence from %s, "
                                   "the sequence will be available after "
                                   "processing at %s", sequence.path,
                                   self.login_controller.osc_api.sequence_link(sequence))
                else:
                    LOGGER.warning("    Failed sequence at %s", sequence.path)
            LOGGER.warning("Finished uploading")
            self.progress_bar.close()


class SequenceUploadOperation:
    """SequenceUploadOperation is a class that is responsible with uploading a sequence to
    OSC servers"""
    def __init__(self, manager: OSCUploadManager, user_token: str, workers: int = 5):
        self.user_token = user_token
        self.workers = workers
        self.manager = manager

    def __eq__(self, other):
        if isinstance(other, SequenceUploadOperation):
            return self.user_token == other.user_token and self.workers == other.workers
        return False

    def __hash__(self):
        return hash(self.user_token, self.workers)

    def upload(self, sequence: Sequence) -> (bool, Sequence):
        """"This method will upload a sequence of video items to OSC servers.
        It returns a success status as bool and the sequence model that was used for the request"""
        if constants.UPLOAD_FINISHED in sequence.progress:
            return True, sequence

        if not sequence.online_id:
            result, online_id = self._create_online_sequence_id(sequence)
            if result:
                sequence.online_id = online_id
            else:
                return False, sequence

        visual_item_upload_operation = PhotoUploadOperation(self.manager,
                                                            self.user_token,
                                                            sequence.online_id)
        if sequence.visual_data_type == "video":
            visual_item_upload_operation = VideoUploadOperation(self.manager,
                                                                self.user_token,
                                                                sequence.online_id)
        self._visual_items_upload_with_operation(sequence, visual_item_upload_operation)

        if len(sequence.progress) == len(sequence.visual_items):
            osc_api = self.manager.login_controller.osc_api
            response, _ = osc_api.finish_upload(sequence, self.user_token)
            if response:
                self.__persist_upload_index(constants.UPLOAD_FINISHED, sequence.path)
                return True, sequence
        return False, sequence

    def _create_online_sequence_id(self, sequence) -> (bool, Sequence):
        osc_sequence = OSCSequence()
        osc_sequence.local_id = sequence.path
        osc_sequence.metadata_url = sequence.osc_metadata
        osc_sequence.latitude = sequence.latitude
        osc_sequence.longitude = sequence.longitude
        osc_api = self.manager.login_controller.osc_api
        online_id, error = osc_api.create_sequence(osc_sequence, self.user_token)
        if error:
            return False, online_id
        self.__persist_squence_id(sequence.online_id, sequence.path)
        return True, online_id

    def _visual_items_upload_with_operation(self, sequence, visual_item_upload_operation):
        items_to_upload = []
        for visual_item in sequence.visual_items:
            if str(visual_item.index) not in sequence.progress:
                items_to_upload.append(visual_item)

        with THREAD_LOCK:
            self.manager.progress_bar.update(len(sequence.visual_items) - len(items_to_upload))

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_events = [executor.submit(visual_item_upload_operation.upload,
                                             visual_item) for visual_item in items_to_upload]
            for completed_event in as_completed(future_events):
                uploaded, index = completed_event.result()
                with THREAD_LOCK:
                    if uploaded:
                        self.__persist_upload_index(index, sequence.path)
                        sequence.progress.append(index)
                    self.manager.progress_bar.update(1)

    @classmethod
    def __persist_squence_id(cls, sequence_id, path):
        LOGGER.debug("will save sequence_id into file")
        sequence_dict = {"id": sequence_id}
        with open(path + "/osc_sequence_id.txt", 'w') as output:
            json.dump(sequence_dict, output)
            LOGGER.debug("Did write data to sequence_id file")

    @classmethod
    def __persist_upload_index(cls, sequence_index, path):
        LOGGER.debug("will save upload index into file")
        with open(path + "/osc_sequence_upload_progress.txt", 'a') as output:
            output.write(str(sequence_index) + ";")


class VideoUploadOperation:
    """VideoUploadOperation is a class responsible with making a video upload."""

    def __init__(self, manager: OSCUploadManager, user_token: str, sequence_id: str):
        self.sequence_id = sequence_id
        self.user_token = user_token
        self.manager = manager

    def __eq__(self, other):
        if isinstance(other, VideoUploadOperation):
            return self.user_token == other.user_token and self.sequence_id == other.sequence_id
        return False

    def __hash__(self):
        return hash(self.user_token, self.sequence_id)

    def upload(self, video: Video) -> (bool, int):
        """This method will upload the video corresponding to the video model
        received as parameter. It returns a tuple: success as bool and video index as int"""
        user = self.manager.login_controller.user
        api = self.manager.login_controller.osc_api

        uploaded = False
        for _ in range(0, 10):
            uploaded, _ = api.upload_video(user.access_token,
                                           self.sequence_id,
                                           video.path,
                                           video.index)
            if uploaded:
                break
            LOGGER.debug("Will request upload %s", video.path)

        return uploaded, video.index


class PhotoUploadOperation:
    """PhotoUploadOperation is a class responsible with making a photo upload."""

    def __init__(self, manager: OSCUploadManager, user_token: str, sequence_id: str):
        self.user_token = user_token
        self.sequence_id = sequence_id
        self.manager = manager

    def __eq__(self, other):
        if isinstance(other, PhotoUploadOperation):
            return self.user_token == other.user_token and self.sequence_id == other.sequence_id
        return False

    def __hash__(self):
        return hash(self.user_token, self.sequence_id)

    def upload(self, photo: Photo) -> (bool, int):
        """This method will upload the image corresponding to the photo model
        received as parameter. It returns a tuple: success as bool and photo index as int"""
        user = self.manager.login_controller.user
        api = self.manager.login_controller.osc_api

        osc_photo = OSCPhoto()
        osc_photo.image_name = str(photo.index) + ".jpg"
        osc_photo.latitude = photo.latitude
        osc_photo.longitude = photo.longitude
        osc_photo.compass = photo.gps_compass
        osc_photo.sequence_index = photo.index

        uploaded = False
        for _ in range(0, 10):
            uploaded, _ = api.upload_photo(user.access_token,
                                           self.sequence_id,
                                           osc_photo,
                                           photo.path)
            if uploaded:
                break
            LOGGER.debug("Will request upload %s", photo.path)

        return uploaded, photo.index
