"""
Used to sort files in several folders.
It is based on timestamp
"""
import argparse
import os
import sys
import shutil
from datetime import datetime
from calendar import timegm
from operator import itemgetter
import exifread


def get_exif(file_path):
    """
    :param file_path: path to file
    :return: timestamp by exif
    """
    with open(file_path, 'rb') as fh:
        tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
        date_taken = tags["EXIF DateTimeOriginal"]
        return date_taken


def create_folders(file_list, folder_dest, folder_src):
    """
    Function that move files into destination folder
    :param file_list: list with files tha will be moved
    :param folder_dest: destination folder
    :param folder_src: source folder
    :return: empty list
    """
    os.mkdir(folder_dest)
    for photo_name in file_list:
        shutil.move(folder_src + '/' + photo_name, folder_dest + '/' + photo_name)
    return []


def main(folder_path):
    """
    Main function that will create and sort the files
    :param folder_path: path to folder that contain files for sort
    :return: None
    """
    if os.path.basename(folder_path) != "":
        folder_path += "/"
    photos_path = os.listdir(folder_path)
    time_stamp_list = []
    for photo_path in [p for p in photos_path]:
        if ('jpg' in photo_path.lower() or 'jpeg' in photo_path.lower()) \
                and "thumb" not in photo_path.lower():
            try:
                time_stamp_list.append({"file": photo_path,
                                        "timestamp": get_exif(folder_path + photo_path).values})
            except Exception as ex:
                print("Error " + str(photo_path) + " not support this exifread module read type")
                print(ex)
                sys.exit()
    time_stamp_list = sorted(time_stamp_list, key=itemgetter('timestamp'))
    fmt = '%Y:%m:%d %H:%M:%S'
    default_time = timegm(datetime.strptime(time_stamp_list[0]['timestamp'], fmt).utctimetuple())
    listed_files = []
    exist_list = False
    for elem in time_stamp_list:
        if 'jpg' in elem['file'].lower() or 'jpeg' in elem['file'].lower():
            tm = elem['timestamp']
            photo_timestamp = timegm(datetime.strptime(tm, fmt).utctimetuple())
            if default_time - photo_timestamp < -30:
                listed_files = create_folders(listed_files,
                                              folder_path + str(default_time),
                                              folder_path)
                default_time = photo_timestamp
                listed_files.append(elem['file'])
                exist_list = True
            else:
                default_time = photo_timestamp
                listed_files.append(elem['file'])
    if listed_files is not None and exist_list is True:
        listed_files = create_folders(listed_files, folder_path + str(default_time), folder_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, help="Full path to files ", required=True)
    args = parser.parse_args()
    full_path_to_folder = args.path
    main(full_path_to_folder)
