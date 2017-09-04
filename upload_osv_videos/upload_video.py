#!/usr/bin/env python
import os
import argparse
from osc.metadata_parser import parse_csv
from osc.osc_actions import get_osc_url
from osc.osc_actions import finish_upload
from osc.osm_access import get_access_token
from osc.sequence import get_sequence
from osc.utils import get_metadata_path, open_metadata
from osc.utils import create_metadata_backup
from upload_osv_videos.video import upload_videos

# Working for and track.txt
# Working for iOS and Android metaData file


def get_args():
    """Parse ARGUMENTS."""
    arg = argparse.ArgumentParser(
        description='Retrieve OpenStreetCam imagery')
    arg.add_argument(
        '-p',
        '--path',
        required=True,
        help='Full path directory that contains videos',
        default=None)
    arg.add_argument(
        '-r',
        '--run',
        help='Test only',
        required=False)
    return arg.parse_args()


def main():
    args = get_args()
    run = args.run
    path = args.path

    url_sequence, url_video, url_finish, url_access = get_osc_url(run, 'video')

    access_token = get_access_token(url_access)

    folders = os.listdir(path)

    for folder in folders:
        dir_path = path + "/" + folder
        if os.path.isfile(dir_path + "/track.txt") or os.path.isfile(dir_path + "/track.txt.gz"):
            print("Processing directory: " + str(folder))
            metadata_name, metadata_type, index_write = get_metadata_path(dir_path)
            firs_id_sequence = create_metadata_backup(index_write)
            metadata = open_metadata(dir_path, metadata_name)
            sensor_data = parse_csv(metadata, 'video')
            files = {'metaData': (metadata_name, open(dir_path + '/' + metadata_name, "rb"), metadata_type)}
            id_sequence = get_sequence(dir_path + '/', '', access_token, url_sequence, sensor_data=sensor_data,
                                       file=files)
            if id_sequence is not None:
                upload_videos(url_video, sensor_data, dir_path, firs_id_sequence, access_token, id_sequence,
                              index_write)
                finish_upload(url_finish, dir_path + '/', access_token, id_sequence)
            else:
                continue


if __name__ == "__main__":
    main()
