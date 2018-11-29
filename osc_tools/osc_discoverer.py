#!/usr/bin/python
"""This script is used to discover video files, sensor info and return Sequences."""
from pablo.osc_tools.visual_data_discover import VisualDataDiscoverer

class Sequence:
    """Model class for a sequence"""

    def __init__(self):
        self.online_id: str = ""
        self.visual_data: [str] = []
        self.osc_metadata: str = ""
        self.visual_data_type: str = ""

    @property
    def description(self) -> str:
        """this method returns a string description of a sequence"""
        return self.online_id + self.osc_metadata + self.visual_data_type

    def visual_data_count(self) -> int:
        """this method returns the count of visual data"""
        return len(self.visual_data)


class OptionalMetadata:
    """In memory representation of movement related data from osc metadata"""

    def __init__(self):
        self.accelerometer_data: [str] = []
        self.attitude_data: [str] = []
        self.pressure_data: [str] = []
        self.obd_data: [str] = []
        self.compass: [str] = []

    @property
    def description(self) -> str:
        """this method returns a string description of a sequence"""
        return str(len(self.accelerometer_data)) + str(len(self.attitude_data)) \
               + str(len(self.pressure_data))

    def __eq__(self, other):
        if isinstance(other, OptionalMetadata):
            return self.accelerometer_data == other.accelerometer_data
        return False


class RequiredMetadata:
    """class to create in memory representation of a most basic osc metadata"""

    def __init__(self):
        self.gps_data: [str] = []
        self.photo_data: [str] = []
        self.video_data: [str] = []
        self.device_data: [str] = []

    @property
    def description(self) -> str:
        """this method returns a string description of a sequence"""
        return str(len(self.gps_data)) + str(len(self.photo_data)) + str(len(self.video_data))

    def __eq__(self, other):
        if isinstance(other, RequiredMetadata):
            return self.gps_data == other.gps_data
        return False

    def has_gps(self) -> bool:
        """method tha returns if this metadata contains gps"""
        return len(self.gps_data) > 0


class MetadataParser:
    """Class to create in memory representation of metadata"""

    def __init__(self):
        self.basic_metadata = RequiredMetadata()
        self.movement_metadata = OptionalMetadata()
        self.camera_data: [str] = []

    def parse(self, path: str) -> bool:
        """This method will parse the file form path and extract osc metadata information
        form that file
        """
        print("the path to parse metadata" + path)
        self.basic_metadata.gps_data = []
        return False

    @property
    def device_name(self):
        """this method return device name form the metadata"""
        return self.basic_metadata.device_data[0]


class SequenceValidator:
    """This class checks if a Sequence will be accepted on the OSC server as a valid sequence"""

    def __init__(self):
        self.metadata_parser = MetadataParser()

    def validate(self, sequence: Sequence) -> bool:
        """this method returns is a bool that. If it returns True the sequence is valid if returns
        False the sequence is not valid and it is not usable for OSC servers.
        """
        self.metadata_parser.parse(sequence.osc_metadata)
        if not self.metadata_parser.basic_metadata.has_gps():
            print('no gps data')

        return self.check_sequence(sequence)

    def check_sequence(self, sequence: Sequence) -> bool:
        """This method checks if the sequence contains coherent data. Returns True if the sequence
        is coherent and False if not.
        """
        if len(self.metadata_parser.basic_metadata.video_data) == len(sequence.visual_data):
            print('metadata is consistent with sequence visual data')
        if sequence.online_id == "":
            print('no online id')
        elif sequence.visual_data == "":
            print('no visual data')
        return False


class OSCMetadataDiscoverer:
    """this class will discover a metadata file"""

    @classmethod
    def discover(cls, path: str) -> str:
        """This method will discover osc metadata path"""
        metadata = ""
        print("discovered metadata")
        print(path)
        return metadata

    @classmethod
    def discover_using_type(cls, path: str, osc_type: str):
        """this method is discovering the online id"""
        print(path)
        print(osc_type)


class OnlineIDDiscoverer:
    """This class will discover online id of a sequence"""

    @classmethod
    def discover(cls, path: str) -> str:
        """This method will discover online id"""
        online_id = ""
        print("discovered online id")
        print(path)
        return online_id

    @classmethod
    def discover_using_type(cls, path: str, osc_type: str):
        """this method is discovering the online id"""
        print(path)
        print(osc_type)


class SequenceDiscoverer:
    """Seq discoverer base class"""

    def __init__(self):
        self.online_id: OnlineIDDiscoverer()
        self.visual_data: VisualDataDiscoverer()
        self.osc_metadata: OSCMetadataDiscoverer()
        self.sequences: [Sequence] = []
        self.validator: SequenceValidator = SequenceValidator()

    def discover(self, path: str) -> [Sequence]:
        """This method will discover a valid sequence"""
        print("discovered sequences")
        sequence = Sequence()
        self.discover_sequence_attributes(path, sequence)
        self.validator.validate(sequence)
        return []

    def discover_sequence_attributes(self, path, sequence):
        """This method will discover all attributes af a sequence"""
        sequence.online_id = self.online_id.discover(path)
        (visual_data, data_type) = self.visual_data.discover(path)
        sequence.osc_metadata = self.osc_metadata.discover(path)
        sequence.visual_data = visual_data
        sequence.visual_data_type = data_type


class SequenceDiscovererFactory:
    """Class that builds a list of sequence discoverers ready to use."""

    @classmethod
    def discoverers(cls) -> [SequenceDiscoverer]:
        """This is a factory method that will return Sequence Discoverers"""
        return [cls.photo_discoverer()]

    @classmethod
    def photo_discoverer(cls) -> SequenceDiscoverer:
        """This method will return a photo discoverer"""
        return SequenceDiscoverer()
