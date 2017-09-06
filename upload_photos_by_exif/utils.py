import json
from operator import itemgetter
import os


def get_photos_list(path):
    from exif_processing import get_exif
    local_dirs = os.listdir()
    if str(path).replace('/', '') in local_dirs:
        path = os.getcwd() + '/' + path
    if os.path.basename(path) != "":
        path += "/"

    old_dir = os.getcwd()
    os.chdir(path)
    photos_path = sorted(os.listdir(path), key=os.path.getmtime)
    os.chdir(old_dir)
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


def get_uploaded_photos(path):
    count_list = []
    count = 0
    if os.path.isfile(path + "count_file.txt"):
        count_file = open(path + "count_file.txt", "r")
        lines = count_file.readlines()
        for line in lines:
            count_list.append(int(line.replace('\n', '').replace('\r', '')))
            count = int(line.replace('\n', '').replace('\r', ''))

    return count, count_list


def get_data_from_json(path, photo_name):
    folder_name = os.path.basename(path[:-1])
    json_path = path.replace(folder_name, 'cameras/internal')
    json_file = json_path + photo_name.replace('jpg', 'json')
    with open(json_file) as data_file:
        json_data = json.load(data_file)
    try:
        lat = json_data['MAPLatitude']
        lon = json_data['MAPLongitude']
        comapss = json_data['MAPCompassHeading']['TrueHeading']
    except:
        lat = None
        lon = None
        comapss = 1
    return lat, lon, comapss


def photos_to_upload(photos_path):
    nr_photos_upload = 0
    for photo_path in [p for p in photos_path]:
        if ('jpg' in photo_path.lower() or 'jpeg' in photo_path.lower()) and "thumb" not in photo_path.lower():
            nr_photos_upload += 1
    return nr_photos_upload
