#!/usr/bin/env python3
"""This script is used to discover video files, sensor info and return Sequences."""
import os
import json
import logging
import constants
from visual_data_discover import VisualDataDiscoverer
from visual_data_discover import ExifPhotoDiscoverer
from visual_data_discover import PhotoMetadataDiscoverer
from visual_data_discover import VideoDiscoverer
from validators import SequenceValidator, SequenceMetadataValidator, SequenceFinishedValidator
from osc_utils import unzip_metadata
from osc_models import Sequence, Photo


LOGGER = logging.getLogger('osc_tools.osc_discoverer')


class OSCUploadProgressDiscoverer:
    """This class is responsible with finding a upload progress file"""
    def __eq__(self, other):
        if isinstance(other, OSCUploadProgressDiscoverer):
            return self == other
        return False

    def __hash__(self):
        return super().__hash__()

    @classmethod
    def discover(cls, path: str) -> [str]:
        """this method will discover a upload progress file and parse it to get a progress list."""
        LOGGER.debug("will read uploaded indexes")
        progress_file_path = path + "/" + constants.PROGRESS_FILE_NAME
        if not os.path.isfile(progress_file_path):
            return []
        with open(progress_file_path, 'r') as input_file:
            line = input_file.readline()
            indexes = line.split(";")
            return indexes


class OSCMetadataDiscoverer:
    """this class will discover a metadata file"""

    def __eq__(self, other):
        if isinstance(other, OSCMetadataDiscoverer):
            return self == other
        return False

    def __hash__(self):
        return super().__hash__()

    @classmethod
    def discover(cls, path: str) -> str:
        """This method will discover osc metadata path"""
        files = os.listdir(path)
        for file_path in files:
            file_name, file_extension = os.path.splitext(file_path)
            if ".txt" in file_extension and "track" in file_name:
                return path + "/" + file_path
            if ".gz" in file_extension and "track" in file_name:
                return unzip_metadata(path)
        return None
    #     if no metadata found generate metadata from gpx or exif


class OnlineIDDiscoverer:
    """This class will discover online id of a sequence"""

    @classmethod
    def discover(cls, path: str) -> str:
        """This method will discover online id"""
        LOGGER.debug("searching for metadata %s", path)
        sequence_file_path = path + "/osc_sequence_id.txt"
        if not os.path.isfile(sequence_file_path):
            return None

        try:
            with open(sequence_file_path) as json_file:
                data = json.load(json_file)
                if "id" in data and data["id"] and str.isdigit(data["id"]):
                    return int(data["id"])
        except FileNotFoundError:
            return None
        return None

    @classmethod
    def discover_using_type(cls, path: str, osc_type: str):
        """this method is discovering the online id"""
        print(path)
        print(osc_type)


class SequenceDiscoverer:
    """Seq discoverer base class"""
    def __init__(self):
        self.ignored_for_upload: bool = False
        self.name = "default"
        self.online_id: OnlineIDDiscoverer = OnlineIDDiscoverer()
        self.visual_data: VisualDataDiscoverer = VisualDataDiscoverer()
        self.osc_metadata: OSCMetadataDiscoverer = OSCMetadataDiscoverer()
        self.upload_progress: OSCUploadProgressDiscoverer = OSCUploadProgressDiscoverer()
        self.validator: SequenceValidator = SequenceValidator()

    def discover(self, path: str) -> [Sequence]:
        """This method will discover a valid sequence"""
        files = os.listdir(path)
        sequences = []
        for file_path in files:
            full_path = os.path.join(path, file_path)
            if os.path.isdir(full_path):
                sequences = sequences + self.discover(full_path)
        sequence = self.create_sequence(path)
        if self.validator.validate(sequence):
            sequences.append(sequence)
        else:
            LOGGER.debug("This sequence (%s) does not conform to this discoverer %s.", path,
                         self.name)
        return sequences

    def create_sequence(self, path):
        """This method will discover all attributes af a sequence"""
        sequence = Sequence()
        if self.online_id:
            sequence.online_id = self.online_id.discover(path)

        if self.visual_data:
            (visual_data, data_type) = self.visual_data.discover(path)
            sequence.visual_items = visual_data
            sequence.visual_data_type = data_type

        if self.osc_metadata:
            sequence.osc_metadata = self.osc_metadata.discover(path)

        if self.upload_progress:
            sequence.progress = self.upload_progress.discover(path)
        sequence.path = path
        self._find_latitude_longitude(sequence)

        return sequence

    def _find_latitude_longitude(self, sequence: Sequence):
        if not sequence.online_id:
            if sequence.osc_metadata and isinstance(self.validator, SequenceMetadataValidator):
                gps = self.validator.metadata_manager.first_location(sequence.osc_metadata)
                if gps:
                    sequence.latitude = gps.latitude
                    sequence.longitude = gps.longitude
            elif sequence.visual_items:
                visual_item = sequence.visual_items[0]
                if isinstance(visual_item, Photo):
                    sequence.latitude = visual_item.latitude
                    sequence.longitude = visual_item.longitude


class SequenceDiscovererFactory:
    """Class that builds a list of sequence discoverers ready to use."""

    @classmethod
    def discoverers(cls) -> [SequenceDiscoverer]:
        """This is a factory method that will return Sequence Discoverers"""
        return [cls.finished_discoverer(),
                cls.photo_metadata_discoverer(),
                cls.exif_discoverer(),
                cls.video_discoverer()]

    @classmethod
    def photo_metadata_discoverer(cls) -> SequenceDiscoverer:
        """This method will return a photo discoverer"""
        photo_metadata_finder = SequenceDiscoverer()
        photo_metadata_finder.name = "Metadata-Photo"
        photo_metadata_finder.visual_data = PhotoMetadataDiscoverer()
        photo_metadata_finder.validator = SequenceMetadataValidator()
        return photo_metadata_finder

    @classmethod
    def exif_discoverer(cls) -> SequenceDiscoverer:
        """This method will return a photo discoverer"""
        exif_photo_finder = SequenceDiscoverer()
        exif_photo_finder.name = "Exif-Photo"
        exif_photo_finder.visual_data = ExifPhotoDiscoverer()
        exif_photo_finder.osc_metadata = None
        return exif_photo_finder

    @classmethod
    def video_discoverer(cls) -> SequenceDiscoverer:
        """this method will return a video discoverer"""
        video_finder = SequenceDiscoverer()
        video_finder.name = "Metadata-Video"
        video_finder.visual_data = VideoDiscoverer()
        video_finder.validator = SequenceMetadataValidator()
        return video_finder

    @classmethod
    def finished_discoverer(cls) -> SequenceDiscoverer:
        """this method will return a discoverer that finds all the sequences that finished upload"""
        finished_finder = SequenceDiscoverer()
        finished_finder.name = "Done Uploading"
        finished_finder.ignored_for_upload = True
        finished_finder.visual_data = None
        finished_finder.osc_metadata = None
        finished_finder.validator = SequenceFinishedValidator()
        return finished_finder

