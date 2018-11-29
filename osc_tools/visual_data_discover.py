#!/usr/bin/python
"""This script is used to discover video files, or photo files"""
import os


class VisualDataDiscoverer:
    """this class is a abstract discoverer of visual data files"""

    @classmethod
    def discover(cls, path: str) -> ([str], str):
        """This method will discover visual data"""
        pass

    @classmethod
    def discover_using_type(cls, path: str, osc_type: str):
        """this method is discovering the online visual data knowing the type"""
        pass


class PhotoDataDiscoverer(VisualDataDiscoverer):
    """this class will discover all photo files"""

    @classmethod
    def discover(cls, path: str) -> ([str], str):
        """This method will discover visual data"""
        photo_paths = []
        print(path)
        return photo_paths, "photo"

    @classmethod
    def discover_using_type(cls, path: str, osc_type: str):
        """this method is discovering the online id"""
        print(path)
        print(osc_type)

    def get_photos_list(path):
        local_dirs = os.listdir()
        if str(path).replace('/', '') in local_dirs:
            path = os.getcwd() + '/' + path
        if os.path.basename(path) != "":
            path += "/"

        old_dir = os.getcwd()
        photos_path = sorted(os.listdir(path), key=os.path.getmtime)
        time_stamp_list = []
        exist_timestamp = True

        # Sort by exif DateTimeOriginal
        for photo_path in [p for p in photos_path]:
            if ('jpg' in photo_path.lower() or 'jpeg' in photo_path.lower()) and "thumb" not in photo_path.lower():
                try:
                    time_stamp_list.append({"file": photo_path, "timestamp": get_exif(path + photo_path).values})
                except:
                    exist_timestamp = False
                    photos_path = sorted(os.listdir(path), key=itemgetter(1, 2))
        if exist_timestamp:
            time_stamp_list = sorted(time_stamp_list, key=itemgetter('timestamp'))
            photos_path = []
            for element in time_stamp_list:
                photos_path.append(element['file'])

        if "sequence_file.txt" in photos_path:
            photos_path.remove("sequence_file.txt")

        return photos_path

