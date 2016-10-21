#!/usr/bin/env python
# Python 3 only support

__author__ = "Racasan Bogdan"
import getopt
import os
import exifread
import requests
import http.cookiejar
import urllib.request, urllib.error, urllib.parse
import sys
from rauth import OAuth1Service
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import concurrent.futures
from operator import itemgetter
import warnings
import json

COUNT_TO_WRITE = 0
PATH = None


def get_exif(path):
    import exifread
    with open(path, 'rb') as fh:
        tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
        dateTaken = tags["EXIF DateTimeOriginal"]
        return dateTaken


def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)


def get_exif_location(exif_data):
    lat = None
    lon = None

    gps_latitude = _get_if_exist(exif_data, 'GPS GPSLatitude')
    gps_latitude_ref = _get_if_exist(exif_data, 'GPS GPSLatitudeRef')
    gps_longitude = _get_if_exist(exif_data, 'GPS GPSLongitude')
    gps_longitude_ref = _get_if_exist(exif_data, 'GPS GPSLongitudeRef')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degress(gps_latitude)
        if gps_latitude_ref.values[0] != 'N':
            lat = 0 - lat

        lon = _convert_to_degress(gps_longitude)
        if gps_longitude_ref.values[0] != 'E':
            lon = 0 - lon

    return lat, lon


def get_gps_lat_long_compass(path_image):
    image = Image.open(path_image)
    try:
        info = image._getexif()
    except Exception as e:
        e
    if info:
        exif_data = {}
        for tag, value in list(info.items()):
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
        exif_data_gpsInfo = exif_data.get('GPSInfo')
        if not exif_data_gpsInfo:
            raise ValueError("No GPS metadata found.")
        try:
            lat = exif_data_gpsInfo['GPSLatitude']
        except Exception as ex:
            erro = 1
        try:
            long = exif_data_gpsInfo['GPSLongitude']
        except Exception as ex:
            erro = 1

        try:
            if lat and int:
                lat = (float(lat[0][0]) / float(lat[0][1]) + float(lat[1][0]) / float(lat[1][1]) / 60.0 + float(
                    lat[2][0]) / float(lat[2][1]) / 3600.0)
                long = (
                    float(long[0][0]) / float(long[0][1]) + float(long[1][0]) / float(long[1][1]) / 60.0 + float(
                        long[2][0]) / float(long[2][1]) / 3600.0)
            if exif_data_gpsInfo['GPSLatitudeRef'] == 'S':
                lat = 0 - lat
            if exif_data_gpsInfo['GPSLongitudeRef'] == 'W':
                long = 0 - long
        except Exception as ex:
            erro = 1
        try:
            compas = exif_data_gpsInfo['GPSImgDirection']
            compas = compas[0] / compas[1]
        except Exception:
            try:
                compas = exif_data_gpsInfo['GPSTrack']
                compas = compas[0] / compas[1]
            except Exception:
                compas = -1
        return lat, long, compas


def upload_photos(url_photo, dict, timeout, path):
    photo = dict['photo']
    data_photo = dict['data']
    name = dict['name']
    conn = requests.post(url_photo, data=data_photo, files=photo, timeout=timeout)
    photo['photo'][1].close()
    with open(path + "count_file.txt", "a+") as fis:
        global COUNT_TO_WRITE
        COUNT_TO_WRITE += 1
        fis.write((str(COUNT_TO_WRITE)) + '\n')
        fis.close()
    return {'json': conn.json(), 'name': name}


def thread(max_workers, url_photo, list_to_upload, path, count_uploaded, total_img):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(upload_photos, url_photo, dict, 1000, path): dict for dict in list_to_upload}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()['json']
                name = future.result()['name']
                print("processing {}".format(name))
                if data['status']['apiCode'] == "600":
                    percentage = float((float(COUNT_TO_WRITE) * 100) / float(total_img))
                    print(("Uploaded - " + str(COUNT_TO_WRITE) + ' of total :' + str(
                        total_img) + ", percentage: " + str(round(percentage, 2)) + "%"))
                elif data['status']['apiCode'] == "610":
                    print("skipping - a requirement arguments is missing for upload")
                elif data['status']['apiCode'] == "611":
                    print("skipping - image does not have GPS location metadata")
                elif data['status']['apiCode'] == "660":
                    print("skipping - duplicate image")
                else:
                    print (data['status'])
                    print("skipping - bad image")
            except Exception as exc:
                print (exc)
                print ("Uploaded error")
    return count_uploaded


def get_data_from_json(path, photo_name):
    folder_name = os.path.basename(path[:-1])
    json_path = path.replace(folder_name,'cameras/internal')
    json_file = json_path + photo_name.replace('jpg','json')
    with open(json_file) as data_file:
        json_data = json.load(data_file)
    # for row in json_data:
    #     print(row)
    try:
        lat = json_data['MAPLatitude']
        lon = json_data['MAPLongitude']
        comapss = json_data['MAPCompassHeading']['TrueHeading']
    except: 
        lat = None
        lon = None
        comapss = 1
    return lat, lon, comapss

def main(argv):
    try:
        read_input = raw_input
    except NameError:
        read_input = input
    try:
        opts, args = getopt.getopt(argv, "hp:r:t:", ["path=", "run="])
    except getopt.GetoptError:
        print ('upload_photos_by_exif3.py -p <path>')
        sys.exit(2)
    if opts == []:
        print ('upload_photos_by_exif3.py -p <path>')
        sys.exit()
    elif "-p" != opts[0][0] and opts[0][0] != "-h":
        print ('upload_photos_by_exif3.py -p <path>')
        sys.exit()
    elif "-p" != opts[0][0] and opts[0][0] != "-h":
        print ('upload_photos_by_exif3.py -p <path>')
        sys.exit()
    else:
        for opt, arg in opts:
            if opt == '-h':
                print ("")
                print ("Usage:")
                print ('    upload_photos_by_exif3.py -p <path> -r <run> ')
                print ("-General Options:")
                print ("    -h                         Show help.")
                print ("    -p   --path                Full path directory that contains photos")
                print ("    -t   --thread              Set number of thread min = 1, max = 10, default = 4")
                print ("-Optional:")
                print ("    -r   --run                 This upload pictures on: http://openstreetview.com/")
                print (
                    "    -r   --run staging         This upload pictures on: http://staging.openstreetview.com")
                print (
                    "    -r   --run test            This upload pictures on: http://testing.openstreetview.com/")
                print ("Example: ")
                print ("    python upload_photos_by_exif3.py -p /Users/example/Desktop/Photos/ ")
                print ("    python upload_photos_by_exif3.py -p /Users/example/Desktop/Photos/ -t 2")
                print ("    python upload_photos_by_exif3.py -p /Users/example/Desktop/Photos/ -r production")
                print ("    python upload_photos_by_exif3.py -p /Users/example/Desktop/Photos/ -r test")
                print ("    python upload_photos_by_exif3.py -p /Users/example/Desktop/Photos/ -r staging -t 8")

                sys.exit()
            elif opt in ("-p", "--path"):
                run = 'prod'
                path = arg
                max_workers = 4
            elif opt in ("-r", "--run"):
                run = arg
            elif opt in ("-t", "--thread"):
                if int(arg) < 10 and int(arg) > 0:
                    max_workers = int(arg)
                    print("Threads: " + str(max_workers))
                else:
                    max_workers = 4
                    print("Default threads: 4, maximum threads exceeded")
                    # run = "test"
    if run == "test":
        url_sequence = 'http://testing.openstreetview.com/1.0/sequence/'
        url_photo = 'http://testing.openstreetview.com/1.0/photo/'
        url_finish = 'http://testing.openstreetview.com/1.0/sequence/finished-uploading/'
        url_access = 'http://testing.openstreetview.com/auth/openstreetmap/client_auth'
    elif run == "staging":
        url_sequence = 'http://staging.openstreetview.com/1.0/sequence/'
        url_photo = 'http://staging.openstreetview.com/1.0/photo/'
        url_finish = 'http://staging.openstreetview.com/1.0/sequence/finished-uploading/'
        url_access = 'http://staging.openstreetview.com/auth/openstreetmap/client_auth'
    else:
        url_sequence = 'http://openstreetview.com/1.0/sequence/'
        url_photo = 'http://openstreetview.com/1.0/photo/'
        url_finish = 'http://openstreetview.com/1.0/sequence/finished-uploading/'
        url_access = 'http://openstreetview.com/auth/openstreetmap/client_auth'
    global PATH
    PATH = path
    try:
        token_file = open("access_token.txt", "r+")
        string = token_file.read()
        access_token = string
    except Exception as ex:
        osm = OAuth1Service(
            name='openstreetmap',
            consumer_key='rBWV8Eaottv44tXfdLofdNvVemHOL62Lsutpb9tw',
            consumer_secret='rpmeZIp49sEjjcz91X9dsY0vD1PpEduixuPy8T6S',
            request_token_url='http://www.openstreetmap.org/oauth/request_token',
            access_token_url='http://www.openstreetmap.org/oauth/access_token',
            authorize_url='http://www.openstreetmap.org/oauth/authorize',
            signature_obj='',
            base_url='http://www.openstreetmap.org/')

        request_token, request_token_secret = osm.get_request_token()
        authorize_url = osm.get_authorize_url(request_token)
        print ("")
        print ('For login go to this URL in your browser:')
        print (authorize_url)
        print((read_input("Login and  grant acces then press ENTER")))
        cj = http.cookiejar.CookieJar()
        cookies = [{
            "name": "",
            "value": "",
            "domain": "domain",
            "path": "path",
            "secure": "secure",
        }]
        for cookie in cookies:
            c = http.cookiejar.Cookie(version=1,
                                      name=cookie["name"],
                                      value=cookie["value"],
                                      port=None,
                                      port_specified=False,
                                      domain=cookie["domain"],
                                      domain_specified=False,
                                      domain_initial_dot=False,
                                      path=cookie["path"],
                                      path_specified=True,
                                      secure=cookie["secure"],
                                      expires=None,
                                      discard=True,
                                      comment=None,
                                      comment_url=None,
                                      rest={'HttpOnly': None},
                                      rfc2109=False)
            cj.set_cookie(c)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        try:
            opener.open(urllib.request.Request(authorize_url))
        except urllib.error.HTTPError as e:
            print("Can't get osm id")
            print(
                "Please retry and report this issue with the error code on https://github.com/openstreetview/uploader")
            print(e.code)
            print(e.read())
            print(e)
            sys.exit()
        pin = cj._cookies['www.openstreetmap.org']['/']['_osm_session'].value

        try:
            request_token_access, request_token_secret_access = osm.get_access_token(request_token,
                                                                                     request_token_secret,
                                                                                     method='POST',
                                                                                     data={'oauth_verifier': pin})
            data_access = {'request_token': request_token_access,
                           'secret_token': request_token_secret_access
                           }
            resp_access = requests.post(url=url_access, data=data_access)
            access_token = resp_access.json()['osv']['access_token']
            token_file = open("access_token.txt", "w+")
            token_file.write(access_token)
            token_file.close()
        except Exception as ex:
            print (ex)
            print ("ERROR LOGIN no GRANT ACCES")
            sys.exit()

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
                    print (ex)
                    continue
            data_sequence = {'uploadSource': 'Python',
                             'access_token': access_token,
                             'currentCoordinate': str(latitude) + ',' + str(longitude)
                             }
            if latitude is not None and longitude is not None:
                break
    try:
        with open(path + "sequence_file.txt", "r+") as sequence_file:
            id_sequence = sequence_file.read()
            sequence_file.close()
    except Exception as ex:
        with open(path + "sequence_file.txt", "w+") as sequence_file:
            if latitude is None and longitude is None:
                print("Error. There is no latitude and longitude in images.")
                sys.exit()
            h = requests.post(url_sequence, data=data_sequence)
            try:
                id_sequence = h.json()['osv']['sequence']['id']
            except Exception as ex:
                print("Fail code:" + str(ex))
                print("Fail to create the sequence")
                os.remove(path + "sequence_file.txt")
                print("Please restart the script")
                sys.exit()
            sequence_file.write(id_sequence)
            sequence_file.close()
    try:
        photos_path.remove("sequence_file.txt")
    except Exception as ex:
        print("No sequence file existing")
    count_list = []
    try:
        count_file = open(path + "count_file.txt", "r")
        lines = count_file.readlines()
        for line in lines:
            count_list.append(int(line.replace('\n', '')))
            count = int(line.replace('\n', ''))
    except:
        count = 0
    nr_photos_upload = 0
    for photo_path in [p for p in photos_path]:
        if ('jpg' in photo_path.lower() or 'jpeg' in photo_path.lower()) and "thumb" not in photo_path.lower():
            nr_photos_upload += 1
    print("Found " + str(nr_photos_upload) + " pictures to upload")
    local_count = 0
    list_to_upload = []
    int_start = 0
    count_uploaded = count
    global COUNT_TO_WRITE
    COUNT_TO_WRITE = count
    for index in range(int_start, len([p for p in photos_path])):
        photo_to_upload = photos_path[index]
        local_count += 1
        if ('jpg' in photo_to_upload.lower() or 'jpeg' in photo_to_upload.lower()) and \
                        "thumb" not in photo_to_upload.lower() and local_count not in count_list:
            total_img = nr_photos_upload
            photo_name = os.path.basename(photo_to_upload)
            try:
                photo = {'photo': (photo_name, open(path + photo_to_upload, 'rb'), 'image/jpeg')}
                try:
                    latitude, longitude, compas = get_gps_lat_long_compass(path + photo_to_upload)
                except Exception:
                    try:
                        tags = exifread.process_file(open(path + photo_to_upload, 'rb'))
                        latitude, longitude = get_exif_location(tags)
                        compas = -1
                        if latitude is None and longitude is None:
                            latitude, longitude, compas = get_data_from_json(path, photo_path)
                    except Exception:
                        continue
                if compas == -1:
                    # TODO: add 'acces_token': acces_token,
                    data_photo = {'access_token': access_token,
                                  'coordinate': str(latitude) + "," + str(longitude),
                                  'sequenceId': id_sequence,
                                  'sequenceIndex': count
                                  }
                else:
                    data_photo = {'access_token': access_token,
                                  'coordinate': str(latitude) + "," + str(longitude),
                                  'sequenceId': id_sequence,
                                  'sequenceIndex': count,
                                  'headers': compas
                                  }
                info_to_upload = {'data': data_photo, 'photo': photo, 'name': photo_to_upload}
                list_to_upload.append(info_to_upload)
                if count != local_count:
                    count += 1
            except Exception as ex:
                print(ex)
        if (index % 100 == 0 and index != 0) and local_count not in count_list:
            count_uploaded = thread(max_workers, url_photo, list_to_upload, path, count_uploaded, total_img)
            list_to_upload = []
    if (index % 100 != 0) or index == 0:
        count_uploaded = thread(max_workers, url_photo, list_to_upload, path, count_uploaded, nr_photos_upload)

    data_finish = {'access_token': access_token,
                   'sequenceId': id_sequence
                   }
    f = requests.post(url_finish, data=data_finish)
    if f.json()['status']['apiCode'] == '600':
        print(("Finish uploading form dir: " + path + " with sequence id: " + str(id_sequence)))
    else:
        print(("FAIL uploading form dir: " + path))
        print("Error: ")
        print(f.json())


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])
