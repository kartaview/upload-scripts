"""
This is a module for declaring any new custom data classes.
"""
from common.models import PhotoMetadata, GPS


class PhotoGeoJson(PhotoMetadata):
    def __init__(self, gps: GPS, index, relative_path: str):
        super().__init__()
        self.gps = gps
        self.frame_index = index
        self.relative_image_path = relative_path
