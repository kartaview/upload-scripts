#!/usr/bin/env python
import os
import argparse
import __init__
from osc.metadata_parser import parse_csv
from osc.osc_actions import get_osc_url
from osc.osc_actions import finish_upload
from osc.osm_access import get_access_token
from osc.sequence import get_sequence
from osc.utils import get_metadata_path, open_metadata, do_upload

# Working for and track.txt
# Working for iOS and Android metaData file
from upload_osc_apps.upload import UploadOSCApps
from upload_photos_by_exif.utils import get_uploaded_photos


def get_args():
    """Parse ARGUMENTS."""
    arg = argparse.ArgumentParser(
        description='Upload OpenStreetCam videos')
    arg.add_argument(
        '-p',
        '--path',
        required=True,
        help='Full path directory that contains folders with trips',
        default=None)
    arg.add_argument(
        '-t',
        '--thread',
        help='Set number of thread min = 1, max = 10, default = 4',
        default=4,
        required=False)
    arg.add_argument(
        '-r',
        '--run',
        help='Test only',
        required=False)
    return arg.parse_args()


def main():
    args = get_args()
    run = args.run
    path = args.path[:-1] if str(args.path).endswith('/') else str(args.path)
    thread = int(args.thread)

    url_sequence, url_video, url_finish, url_access = get_osc_url(run, 'video')

    access_token = get_access_token(url_access)

    folders = [folder for folder in os.listdir(path) if os.path.isdir(path + "/" + folder)]
    if len(folders) == 0:
        print("Please specify the folder with trips folders")
    for folder in folders:
        dir_path = path + "/" + folder
        if os.path.isfile(dir_path + "/track.txt") or os.path.isfile(dir_path + "/track.txt.gz"):
            print("Processing directory: " + str(folder))
            metadata_name, metadata_type, index_write = get_metadata_path(dir_path)
            metadata = open_metadata(dir_path, metadata_name)
            sensor_data = parse_csv(metadata, 'video')
            files = {'metaData': (metadata_name, open(dir_path + '/' + metadata_name, "rb"), metadata_type)}
            id_sequence = get_sequence(dir_path + '/', '', access_token, url_sequence, sensor_data=sensor_data,
                                       file=files)
            if id_sequence is not None:
                count, count_list = get_uploaded_photos(path)
                result = do_upload(thread, UploadOSCApps(url_video, dir_path, access_token, id_sequence, index_write, count_list), sensor_data)
                if len(result) == len(sensor_data):
                    finish_upload(url_finish, dir_path + '/', access_token, id_sequence)
            else:
                continue
        else:
            print("Please make sure that your folder '{}' includes metadata (track.txt or track.txt.gz)".format(dir_path))

if __name__ == "__main__":
    main()
