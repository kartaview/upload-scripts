#!/usr/bin/env python
# Python 3 only support
import warnings
import sys
import __init__
import argparse
from photo import UploadPhoto
from utils import get_photos_list
from utils import photos_to_upload
from utils import get_uploaded_photos
from osc.osc_actions import finish_upload
from osc.osc_actions import get_osc_url
from osc.osm_access import get_access_token
from osc.sequence import get_sequence
from osc.utils import do_upload


def get_args():
    """Parse ARGUMENTS."""
    arg = argparse.ArgumentParser(
        description='Retrieve OpenStreetCam imagery')
    arg.add_argument(
        '-p',
        '--path',
        required=True,
        help='Full path directory that contains photos',
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
    path = args.path if str(args.path).endswith('/') else str(args.path) + "/"

    thread = int(args.thread)
    url_sequence, url_photo, url_finish, url_access = get_osc_url(run, 'photo')
    access_token = get_access_token(url_access)
    photos_path = get_photos_list(path)
    id_sequence = get_sequence(path, photos_path, access_token, url_sequence)
    if id_sequence is not None:
        count, count_list = get_uploaded_photos(path)
        nr_photos_upload = photos_to_upload(photos_path)

        print("Found " + str(nr_photos_upload) + " pictures to upload")

        do_upload(thread, UploadPhoto(path, access_token, id_sequence, count_list, url_photo), photos_path)

        finish_upload(url_finish, path, access_token, id_sequence)
    else:
        sys.exit()


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
