from osc.osc_actions import make_request
from osc.utils import write_result
from multiprocessing import Value, Lock
from upload_osc_apps.utils import get_data_photo, get_data_video
import time

number = Value('i', 0)
lock = Lock()


class UploadOSCApps(object):
    def __init__(self, url_upload, dir_path, access_token, id_sequence, index_write, count_list):
        self.url_upload = url_upload
        self.dir_path = dir_path
        self.access_token = access_token
        self.id_sequence = id_sequence
        self.index_write = index_write
        self.count_list = count_list

    def __call__(self, sensor):
        lock.acquire()
        time.sleep(0.100)
        lock.release()
        if 'photo' in self.url_upload:
            if sensor['index'] not in self.count_list:
                data_photo, photo = get_data_photo(sensor, self.access_token, self.id_sequence, int(sensor['index']), self.dir_path)
                response = make_request(self.url_upload, data_photo, photo, 'photo')
                if response == 660:
                    return
                write_result(response, self.index_write, sensor, 'photo')
        else:
            if sensor['index'] not in self.count_list:
                data_video, video = get_data_video(sensor, self.access_token, self.id_sequence, self.dir_path)
                response = make_request(self.url_upload, data_video, video, 'video')
                if response == 660:
                    return
                write_result(response, self.index_write, sensor, 'video')
