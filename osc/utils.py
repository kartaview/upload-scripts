import gzip
import os
from multiprocessing import Pool
import tqdm
import sys


def get_metadata_path(path):
    metadata_name = None
    metadata_type = None
    print("{}/track.txt".format(path))
    if os.path.isfile("{}/track.txt".format(path)):
        metadata_name = 'track.txt'
        metadata_type = 'text/plain'
    elif os.path.isfile("{}/track.txt.gz".format(path)):
        metadata_name = 'track.txt.gz'
        metadata_type = 'gzip'
    dst = '{}/count_file.txt'.format(path)
    return metadata_name, metadata_type, dst


def create_metadata_backup(dst):
    firs_id_sequence = -1
    if os.path.isfile(dst):
        print("Metadata backup found")
        with open(dst, "r+") as file:
            index_write = file.readlines()
        for i in index_write:
            firs_id_sequence = int(i)
    else:
        print("Generating metadata backup")
        firs_id_sequence = -1

    return firs_id_sequence


def open_metadata(dir_path, metadata_name):
    backup_path = dir_path + '/' + metadata_name
    if "gz" in metadata_name:
        metadata = gzip.open(backup_path, "r")
    else:
        metadata = open(backup_path, "r")
    return metadata


def write_result(response, index_write, type_data, type_upload):
    try:
        if int(response.json()['osv'][type_upload]['id']) != "":
            img_index = type_data['index']
            with open(index_write, 'a') as index_file:
                index_file.write(str(img_index) + "\n")
    except:
        print("Err for: " + type_data['index'] + ".mp4 with message: " + str(response.json()['status']['apiMessage']))


def exception_firs_id_sequence(ex, index_write):
    if str(ex) == "local variable 'firs_id_sequence' referenced before assignment":
        print("Index file is corrupted")
        print("The index file will be deleted and start from the first photo")
        print("Please restart the script")
        os.remove(index_write)
        sys.exit()


def do_upload(max_workers, generator, payload):
    with Pool(max_workers) as p:
        list(tqdm.tqdm(p.imap(generator, payload), total=len(payload), bar_format='{l_bar}{bar} {n_fmt}/{total_fmt} remaining:{remaining}  elapsed:{elapsed}'))
