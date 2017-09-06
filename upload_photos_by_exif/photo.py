import exifread
import requests
from multiprocessing import Value, Lock
from exif_processing import get_gps_lat_long_compass
from exif_processing import get_exif_location
from utils import get_data_from_json

number = Value('i', 0)
lock = Lock()


class UploadPhoto(object):
    def __init__(self, path, access_token, id_sequence, count_list, url_photo):
        self.url_photo = url_photo
        self.count_list = count_list
        self.id_sequence = id_sequence
        self.access_token = access_token
        self.path = path

    def get_photo_details(self, photo):
        photo_path = self.path + photo
        try:
            latitude, longitude, compas = get_gps_lat_long_compass(photo_path)
        except Exception:
            try:
                tags = exifread.process_file(open(photo_path, 'rb'))
                latitude, longitude = get_exif_location(tags)
                compas = -1
                if latitude is None and longitude is None:
                    latitude, longitude, compas = get_data_from_json(self.path, photo_path)
            except Exception:
                return None
        return latitude, longitude, compas

    def get_data_photo(self, compass, latitude, longitude, count):
        if compass == -1:
            data_photo = {'access_token': self.access_token,
                          'coordinate': str(latitude) + "," + str(longitude),
                          'sequenceId': self.id_sequence,
                          'sequenceIndex': count
                          }
        else:
            data_photo = {'access_token': self.access_token,
                          'coordinate': str(latitude) + "," + str(longitude),
                          'sequenceId': self.id_sequence,
                          'sequenceIndex': count,
                          'headers': compass
                          }
        return data_photo

    def write_count_file(self, data_photo):
        with open(self.path + "count_file.txt", "a+") as fis:
            fis.write((str(data_photo['sequenceIndex'])) + '\n')
            fis.close()

    def make_upload(self, photo, data_photo):
        load_photo = {'photo': (photo, open(self.path + photo, 'rb'), 'image/jpeg')}
        conn = requests.post(self.url_photo, data=data_photo, files=load_photo, timeout=1000)
        if int(conn.status_code) != 200:
            if conn.json()['status']['apiMessage'] == ' You are not allowed to add a duplicate entry (sequenceIndex)':
                self.write_count_file(data_photo)
                return 0
            print("Request/Response fail")
            retry_count = 0
            while int(conn.status_code) != 200:
                print("Retry attempt : " + str(retry_count))
                conn = requests.post(self.url_photo, data=data_photo, files=load_photo, timeout=1000)
                retry_count += 1
        self.write_count_file(data_photo)

    def __call__(self, photo):
        number.value += 1
        count = number.value
        if ('jpg' in photo.lower() or 'jpeg' in photo.lower()) and "thumb" not in photo.lower() and count not in self.count_list:
            if self.get_photo_details(photo) is None:
                return 0
            latitude, longitude, compass = self.get_photo_details(photo)
            data_photo = self.get_data_photo(compass, latitude, longitude, count)
            self.make_upload(photo, data_photo)