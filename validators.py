"""This file will contain all validators used to validate a sequence"""

import logging
import constants
from metadata_manager import MetadataManager, MetadataParser
from metadata_parser import Photo
from osc_models import Sequence, Video


LOGGER = logging.getLogger('osc_tools.validators')


class SequenceValidator:
    """This class checks if a Sequence will be accepted on the OSC server as a valid sequence"""

    def __eq__(self, other):
        if isinstance(other, SequenceValidator):
            return self == other
        return False

    def __hash__(self):
        return super().__hash__()

    def validate(self, sequence: Sequence) -> bool:
        """This method returns is a bool. If it returns True the sequence is valid if returns
        False the sequence is not valid and it is not usable for OSC servers.
        """
        LOGGER.debug("  Validating sequence using %s", str(self.__class__))
        if not sequence.visual_items and not sequence.online_id:
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

    def __init__(self):
        self.metadata_manager: MetadataManager = MetadataManager()

    def __eq__(self, other):
        if isinstance(other, SequenceMetadataValidator):
            return self == other
        return False

    def __hash__(self):
        return super().__hash__()

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
            parser: MetadataParser = self.metadata_manager.get_metadata_parser(metadata_path)
            photo_item = parser.next_item_with_class(Photo)
            if not photo_item:
                LOGGER.debug(" No photo in metadata")
                return False
            recording_type = parser.recording_type()
            visual_item = sequence.visual_items[0]

            if recording_type:
                if recording_type == "video" and not isinstance(visual_item, Video):
                    return False
                if recording_type == "photo" and not isinstance(visual_item, Photo):

                    return False
        return True


class SequenceFinishedValidator(SequenceValidator):
    """SequenceFinishedValidator is a SequenceValidator that is responsible to validate a
    finished sequence"""

    def __eq__(self, other):
        if isinstance(other, SequenceFinishedValidator):
            return self == other
        return False

    def __hash__(self):
        return super().__hash__()

    def validate(self, sequence: Sequence) -> bool:
        """this method will return true if a sequence is already uploaded and was flagged
        as finished"""
        if sequence.progress and \
                constants.UPLOAD_FINISHED in sequence.progress:
            return True
        return False


class SequenceToFinishValidator(SequenceValidator):
    """SequenceToFinishValidator is a SequenceValidator that is responsible to validate
    a sequence that requires only the finish request"""

    def __eq__(self, other):
        if isinstance(other, SequenceToFinishValidator):
            return self == other
        return False

    def __hash__(self):
        return super().__hash__()

    def validate(self, sequence: Sequence) -> bool:
        """This method will return true if a sequence is already uploaded but it was
        not flagged as finished"""
        if sequence.online_id and sequence.progress and \
                constants.UPLOAD_FINISHED not in sequence.progress:
            return True
        return False
