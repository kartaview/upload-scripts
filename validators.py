"""This file will contain all validators used to validate a sequence"""

import logging
from typing import cast

import constants
from common.models import PhotoMetadata, OSCDevice, RecordingType
from io_storage.storage import Local
from parsers.osc_metadata.parser import MetadataParser, metadata_parser
from osc_models import Sequence, Video, Photo

LOGGER = logging.getLogger('osc_tools.validators')


class SequenceValidator:
    """This class checks if a Sequence will be accepted on the OSC server as a valid sequence"""

    def __eq__(self, other):
        if isinstance(other, SequenceValidator):
            return self == other
        return False

    def validate(self, sequence: Sequence) -> bool:
        """This method returns is a bool. If it returns True the sequence is valid if returns
        False the sequence is not valid and it is not usable for OSC servers.
        """
        LOGGER.debug("  Validating sequence using %s", str(self.__class__))
        if not sequence.visual_items:
            LOGGER.debug("    Sequence at %s will not be uploaded since we did not find "
                         "any compatible visual data", sequence.path)
            return False

        if (not sequence.latitude or not sequence.longitude) and not sequence.online_id:
            LOGGER.warning("    WARNING: Sequence at %s will not be uploaded. No "
                           "GPS info was found.", sequence.path)
            return False

        return True


class SequenceMetadataValidator(SequenceValidator):
    """SequenceMetadataValidator is a SequenceValidator responsible of validating if a sequence
    that has metadata"""

    def __eq__(self, other):
        if isinstance(other, SequenceMetadataValidator):
            return self == other
        return False

    def validate(self, sequence: Sequence) -> bool:
        """This method returns is a bool, If it returns True the sequence is valid if returns
                False the sequence is not valid and it is not usable for OSC servers.
                """
        if not super().validate(sequence):
            return False
        # is sequence has metadata
        if sequence.osc_metadata and not sequence.online_id:
            metadata_path = sequence.osc_metadata
            LOGGER.debug("        Validating Metadata %s", metadata_path)
            parser: MetadataParser = metadata_parser(metadata_path, Local())
            photo_item = parser.next_item_with_class(PhotoMetadata)
            if not photo_item:
                LOGGER.debug(" No photo in metadata")
                return False
            device: OSCDevice = cast(OSCDevice, parser.next_item_with_class(OSCDevice))
            visual_item = sequence.visual_items[0]

            if device is not None and device.recording_type is not None:
                if device.recording_type == RecordingType.VIDEO and not isinstance(visual_item,
                                                                                   Video):
                    return False
                if device.recording_type == RecordingType.PHOTO and not isinstance(visual_item,
                                                                                   Photo):
                    return False
        return True


class SequenceFinishedValidator(SequenceValidator):
    """SequenceFinishedValidator is a SequenceValidator that is responsible to validate a
    finished sequence"""

    def __eq__(self, other):
        if isinstance(other, SequenceFinishedValidator):
            return self == other
        return False

    def validate(self, sequence: Sequence) -> bool:
        """this method will return true if a sequence is already uploaded and was flagged
        as finished"""
        if sequence.progress and \
                constants.UPLOAD_FINISHED in sequence.progress:
            return True
        return False
