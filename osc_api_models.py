"""This file contains all the osc api models """


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
        self.yaw = None
    # pylint: enable=R0902

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

    # pylint: disable=R0902
    def __init__(self):
        self.photos: [OSCPhoto] = []
        self.local_id: str = None
        self.online_id: str = None
        self.path: str = None
        self.metadata_url = None
        self.latitude = None
        self.longitude = None
        self.platform = None
        self.device = None
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
