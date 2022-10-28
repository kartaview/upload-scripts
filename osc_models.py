"""osc_models module contains all the application level models"""
from typing import Optional

from common.models import CameraProjection


# pylint: disable=R0902

class Sequence:
    """Sequence is a model class containing a list of visual items"""

    def __init__(self):
        self.path: str = ""
        self.online_id: str = ""
        self.progress: [str] = []
        self.visual_items: [VisualData] = []
        self.osc_metadata: str = ""
        self.visual_data_type: str = ""
        self.latitude: float = None
        self.longitude: float = None
        self.platform: Optional[str] = None
        self.device: Optional[str] = None

    @property
    def description(self) -> str:
        """this method returns a string description of a sequence"""
        return self.online_id + self.osc_metadata + self.visual_data_type

    def visual_data_count(self) -> int:
        """this method returns the count of visual data"""
        return len(self.visual_items)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Sequence):
            return self.path == other.path
        return False

    def __hash__(self):
        return hash(self.path)


class VisualData:
    """VisualData is a model class for a visual item"""
    def __init__(self, path):
        self.path: str = path
        self.index: int = None

    def __eq__(self, other):
        if isinstance(other, VisualData):
            return self.path == other.path and \
                   self.index == other.index
        return False

    def __hash__(self):
        return hash((self.path, self.index))


class Photo(VisualData):
    """Photo is a VisualData model for a photo item"""

    # pylint: disable=R0902
    def __init__(self, path):
        super().__init__(path)
        self.latitude: float = None
        self.longitude: float = None
        self.exif_timestamp: float = None
        self.gps_timestamp: float = None
        self.gps_speed: float = None
        self.gps_altitude: float = None
        self.gps_compass: float = None
        self.fov: Optional[float] = None
        self.projection: CameraProjection = None

    # pylint: enable=R0902

    def __eq__(self, other):
        if isinstance(other, Photo):
            return self.gps_timestamp == other.gps_timestamp and \
                   self.latitude == other.path and \
                   self.longitude == other.longitude
        return False

    def __hash__(self):
        return hash((self.gps_timestamp,
                    self.latitude,
                    self.longitude))


class Video(VisualData):
    """Video is a VisualData model for a video item"""
    def __eq__(self, other):
        if isinstance(other, Video):
            return self.path == other.path and self.index == other.index
        return False

    def __hash__(self):
        return hash((self.path, self.index))

# pylint: enable=R0902
