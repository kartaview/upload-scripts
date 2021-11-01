from common.models import PhotoMetadata


class PhotoGeoJson(PhotoMetadata):
    def __init__(self):
        super(PhotoGeoJson, self).__init__()
        self.relative_image_path: Optional[str] = None
