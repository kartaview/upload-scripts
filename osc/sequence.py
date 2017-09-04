import exifread
import os
import sys
import requests


def get_sequence(path, photos_path, access_token, url_sequence, sensor_data=None, file=None):
    if os.path.isfile(path + "sequence_file.txt"):
        with open(path + "sequence_file.txt", "r+") as sequence_file:
            id_sequence = sequence_file.read()
            sequence_file.close()
            return id_sequence
    elif sensor_data is None:
        data_sequence = get_data_to_create_sequence(photos_path, access_token, path)
        id_sequence = create_new_sequence(path, url_sequence, data_sequence)

    else:
        data_sequence = get_data_sequence_osc_apps(access_token, sensor_data)
        id_sequence = create_new_sequence(path, url_sequence, data_sequence, file)
    return id_sequence


def create_new_sequence(path, url_sequence, seq_data, files=None):
    with open(path + "sequence_file.txt", "w+") as sequence_file:
        try:
            if files is None:
                data_sequence = seq_data['data_sequence']
                latitude = seq_data['lat']
                longitude = seq_data['lon']
                if latitude is None and longitude is None:
                    print("Error. There is no latitude and longitude in images.")
                    sys.exit()
                h = requests.post(url_sequence, data=data_sequence)
            else:
                h = requests.post(url_sequence, data=seq_data, files=files)
            id_sequence = h.json()['osv']['sequence']['id']
        except Exception as ex:
            print("Fail code:" + str(ex))
            print("Fail to create the sequence")
            os.remove(path + "sequence_file.txt")
            id_sequence = None
        if id_sequence is not None:
            sequence_file.write(id_sequence)
    return id_sequence


def get_data_to_create_sequence(photos_path, access_token, path):
    from upload_photos_by_exif.exif_processing import get_gps_lat_long_compass
    from upload_photos_by_exif.exif_processing import get_exif_location
    from upload_photos_by_exif.utils import get_data_from_json

    for photo_path in [p for p in photos_path]:
        if ('jpg' in photo_path.lower() or 'jpeg' in photo_path.lower()) and "thumb" not in photo_path.lower():
            try:
                latitude, longitude, compas = get_gps_lat_long_compass(path + photo_path)
            except Exception:
                try:
                    tags = exifread.process_file(open(path + photo_path, 'rb'))
                    latitude, longitude = get_exif_location(tags)
                    if latitude is None and longitude is None:
                        latitude, longitude, compas = get_data_from_json(path, photo_path)
                except Exception as ex:
                    print(ex)
                    continue
            data_sequence = {'uploadSource': 'Python',
                             'access_token': access_token,
                             'currentCoordinate': str(latitude) + ',' + str(longitude)
                             }
            if latitude is not None and longitude is not None:
                break
    return {'lat': latitude, 'lon': longitude, 'data_sequence': data_sequence}


def get_data_sequence_osc_apps(access_token, sensor_data):
    for sensor in sensor_data:
        try:
            app_version = sensor['app_version']
        except:
            app_version = None
        if app_version is None:
            data_sequence = {'uploadSource': 'Python',
                             'access_token': access_token,
                             'currentCoordinate': str(sensor['latitude']) + "," + str(sensor['longitude']),
                             'obdInfo': sensor['obdInfo'],
                             'platformName': sensor['platformName'],
                             'platformVersion': sensor['platformVersion']
                             }
        else:
            data_sequence = {'uploadSource': 'Python',
                             'access_token': access_token,
                             'currentCoordinate': str(sensor['latitude']) + "," + str(sensor['longitude']),
                             'obdInfo': sensor['obdInfo'],
                             'platformName': sensor['platformName'],
                             'platformVersion': sensor['platformVersion'],
                             'appVersion': sensor['appVersion']
                             }
        return data_sequence
