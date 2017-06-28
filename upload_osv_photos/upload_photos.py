#!/usr/bin/env python
__author__ = "Racasan Bogdan"
# Working for track.txt.gz and track.txt
# Working for 1.0.8 version or lower
# Working for iOS and Android metaData file
import getopt
import gzip
import os
import requests
import cookielib
import urllib2
import sys
from rauth import OAuth1Service
import requests

requests.adapters.DEFAULT_RETRIES = 1000

def main(argv):
    try:
        read_input = raw_input
    except NameError:
        read_input = input
    try:
        opts, args = getopt.getopt(argv, "hp:r:", ["path=", "run="])
    except getopt.GetoptError:
        print ('upload_photos.py -p <path>')
        sys.exit(2)
    if opts == []:
        print ('upload_photos.py -p <path>')
        sys.exit()
    elif "-p" != opts[0][0] and opts[0][0] != "-h":
        print ('upload_photos.py -p <path>')
        sys.exit()

    else:
        for opt, arg in opts:
            if opt == '-h':
                print ("")
                print ("Usage:")
                print ('    upload_photos.py -p <path> -r <run> ')
                print ("-General Options:")
                print ("    -h                         Show help.")
                print ("    -p   --path                Full path to main directory that contains the track directories")
                print ("-Optional:")
                print ("    -r   --run                 This upload pictures on: http://openstreetview.com/")
                print (
                    "    -r   --run staging         This upload pictures on: http://staging.open-street-view.skobbler.net")
                print (
                    "    -r   --run test            This upload pictures on: http://tst.open-street-view.skobbler.net/")
                print ("Example: ")
                print ("    python upload_photos.py -p /Users/example/Desktop/Photos/ ")
                print ("    python upload_photos.py -p /Users/example/Desktop/Photos/ -r production")
                print ("    python upload_photos.py -p /Users/example/Desktop/Photos/ -r test")
                print ("    python upload_photos.py -p /Users/example/Desktop/Photos/ -r staging")

                sys.exit()
            elif opt in ("-p", "--path"):
                run = 'prod'
                path = arg
            elif opt in ("-r", "--run"):
                run = arg

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
        cj = cookielib.CookieJar()
        cookies = [{
            "name": "",
            "value": "",
            "domain": "domain",
            "path": "path",
            "secure": "secure",
        }]
        for cookie in cookies:
            c = cookielib.Cookie(version=1,
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
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        ceva = opener.open(urllib2.Request(authorize_url))
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

    # run = "test"


    directory = os.listdir(path)
    for dir in directory:
        if os.path.isfile(path + "/" + dir + "/track.txt") or os.path.isfile(path + "/" + dir + "/track.txt.gz"):
            print("Processing directory: " + str(dir))
            dir_path = path + "/" + dir + "/"
            if os.path.isfile(path + "/" + dir + "/track.txt"):
                metaData_name = 'track.txt'
            elif os.path.isfile(path + "/" + dir + "/track.txt.gz"):
                metaData_name = 'track.txt.gz'
            dst = path + '/' + dir + "/" + 'index_write.txt'

            if os.path.isfile(dst):
                print ("Metadata backup found")
                index_write = file(dst, "r+")
                for i in index_write:
                    firs_id_sequence = int(i)
            else:
                print ("Generating metadata backup")
                index_write = file(dst, "w+")
                firs_id_sequence = -1
                # copyfile(src, dst)
            backup_path = dir_path + metaData_name
            if "gz" in metaData_name:
                metaData = gzip.open(backup_path, "r")
                metaData1 = gzip.open(backup_path, "r")
            else:
                metaData = file(backup_path, "r")
                metaData1 = file(backup_path, "r")
            senzor_data1 = parseCsv(metaData1, backup_path)
            for image in senzor_data1:
                files = {'metaData': (metaData_name, open(dir_path + metaData_name, "rb"), 'text/plain')}
                try:
                    app_version = image_data['app_version']
                except:
                    app_version = None
                data_sequence = {'uploadSource': 'Python',
                                 'access_token': access_token,
                                 'currentCoordinate': str(image['latitude']) + "," + str(image['longitude'])
                                 }

                try:
                    sequence_file = file(dir_path + "sequence_file.txt", "r+")
                    id_sequence = sequence_file.read()
                    break
                except Exception as ex:
                    sequence_file = file(dir_path + "sequence_file.txt", "w+")
                    h = requests.post(url_sequence, data=data_sequence, files=files)
                    id_sequence = h.json()['osv']['sequence']['id']
                    sequence_file.write(id_sequence)
                    sequence_file.close()
                    break

            senzor_data = parseCsv(metaData, backup_path)
            count = 0
            for image_data in senzor_data:
                try:
                    if firs_id_sequence < int(image_data['index']):
                        photo = {'photo': (
                            image_data['index'] + '.jpg', open(dir_path + image_data['index'] + '.jpg', 'rb'),
                            'image/jpeg')}
                        if image_data['compas'] != '':
                            # TODO: add 'acces_token': acces_token,
                            data_photo = {'access_token': access_token,
                                          'coordinate': str(image_data['latitude']) + "," + str(image_data['longitude']),
                                          'sequenceId': id_sequence,
                                          'headers': image_data['compas'],
                                          'gpsAccuracy': image_data['horizontal_accuracy'],
                                          'sequenceIndex': count
                                          }
                        else:
                            data_photo = {'access_token': access_token,
                                          'coordinate': str(image_data['latitude']) + "," + str(image_data['longitude']),
                                          'sequenceId': id_sequence,
                                          'sequenceIndex': count,
                                          'gpsAccuracy': image_data['horizontal_accuracy']
                                          }

                        try:
                            p = requests.post(url_photo, data=data_photo, files=photo)
                        except requests.exceptions.Timeout:
                            print("Timout error  retry:")
                            count_timeout = 0
                            for i in range(0, 9):
                                try:
                                    count_timeout += 1
                                    print("Retry : " + str(i))
                                    p = requests.post(url_photo, data=data_photo, files=photo)
                                    if int(p.json()['osv']['photo']['id']) != "":
                                        break
                                except requests.exceptions.Timeout:
                                    continue
                            if count_timeout == 9:
                                print("Timeout Err")
                                print("To not lose any data the script will stop")
                                print("Please restart the script")
                                sys.exit()
                        except requests.exceptions.ConnectionError:
                            print("Connection Err")
                            print("To not lose any data the script will stop")
                            print("Make sure you have an internet connection then restart the script")
                            sys.exit()
                        try:
                            if int(p.json()['osv']['photo']['id']) != "":
                                count += 1
                                img_index = image_data['index']
                                total_img = senzor_data[len(senzor_data) - 1]['index']
                                percentage = float((float(img_index) * 100) / float(total_img))
                                print ("Uploaded :" + img_index + '.jpg, remaining :' + str(
                                    len(senzor_data) - count) + ", percentage: " + str(round(percentage, 2)) + "%")
                                index_write.write(str(img_index) + "\n")
                                # deletePhoto(dir_path, image_data['index'])
                        except Exception as ex:
                            print ("Err for: " + image_data['index'] + ".jpg with message: " + str(
                                p.json()['status']['apiMessage']))
                except Exception as ex:
                    if str(ex) == "local variable 'firs_id_sequence' referenced before assignment":
                        print ("Index file is corrupted")
                        print ("The index file will be deleted and start from the first photo")
                        print ("Please restart the script")
                        os.remove(dst)
                        sys.exit()
                    print "ERR"
            data_finish = {'access_token': access_token,
                           'sequenceId': id_sequence
                           }
            f = requests.post(url_finish, data=data_finish)
            if f.json()['status']['apiCode'] == '600':
                print ("Finish uploading from dir: " + dir_path)
            else:
                print ("FAIL uploading from dir: " + dir_path)


format = {'1.0.3': {'time': 0, 'compas': 12, 'index': 13, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4},
          '1.0.5': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4},
          '1.0.6': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4,
                    'ODB': 18},
          '1.0.7': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4,
                    'ODB': 18},
          '1.0.8': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4,
                    'ODB': 18},
          'ios_first_version': {'time': 0, 'compas': 1, 'index': 13, 'longitude': 1, 'latitude': 2,
                                'horizontal_accuracy': 4}
          }


def parseCsv(files, backup_path):
    senzor_data = []
    app_version = None
    try:
        read = files.readline().replace(" ", "_")
        device = read.split(";")[0].replace('_', ' ')
        if 'iP' in device:
            version = read.split(';')[2].replace("\n", "")
            if version == "":
                version = 'ios_first_version'
                platformVersion = 'Unknown'
            else:
                try:
                    platformVersion = read.split(';')[1].replace("\n", "")
                except Exception:
                    platformVersion = 'Unknown'
                if version == '1.0.8':
                    app_version = read.split(';')[3].replace("\n", "")
        else:
            version = read.split(';')[2].replace("\n", "")
            if version == "":
                version = 'ios_first_version'
                platformVersion = 'Unknown'
            else:
                try:
                    platformVersion = read.split(';')[1].replace("\n", "")
                except Exception:
                    platformVersion = 'Unknown'
                if version == '1.0.8':
                    app_version = read.split(';')[3].replace("\n", "")
        curent_format = format[version]
        compas = -1
        longitude = 0
        latitude = 0
        horizontal_accuracy = 0
        ODB = 0
        time_compas = 0
        time_longitude = 0
        time_latitude = 0
        time_horizontal_accuracy = 0
        for line in files:
            if "," in line:
                continue
            lines = line.replace("\n", "")
            if lines.split(";")[curent_format['compas']] != '' and time_compas < lines.split(";")[
                curent_format['time']]:
                time_compas = lines.split(";")[curent_format['time']]
                compas = lines.split(";")[curent_format['compas']]
            if lines.split(";")[curent_format['longitude']] != '' and time_longitude < lines.split(";")[
                curent_format['time']]:
                time_longitude = lines.split(";")[curent_format['time']]
                longitude = lines.split(";")[curent_format['longitude']]
            if lines.split(";")[curent_format['latitude']] != '' and time_latitude < lines.split(";")[
                curent_format['time']]:
                time_latitude = lines.split(";")[curent_format['time']]
                latitude = lines.split(";")[curent_format['latitude']]
            if lines.split(";")[curent_format['horizontal_accuracy']] != '' and time_horizontal_accuracy < \
                    lines.split(";")[curent_format['time']]:
                time_horizontal_accuracy = lines.split(";")[curent_format['time']]
                horizontal_accuracy = lines.split(";")[curent_format['horizontal_accuracy']]
            try:
                if lines.split(";")[curent_format['ODB']] != '':
                    ODB = 1
            except Exception as ex:
                ex
            if lines.split(";")[curent_format['index']] != '':
                index = lines.split(";")[curent_format['index']]
                if version == 'ios_first_version':
                    compas = ''
                if app_version is not None:
                    image_data = {"index": index, "compas": compas, "longitude": longitude, "latitude": latitude,
                                  "horizontal_accuracy": horizontal_accuracy, "obdInfo": ODB, 'platformName': device,
                                  'platformVersion': platformVersion,
                                  'appVersion': app_version}
                else:
                    image_data = {"index": index, "compas": compas, "longitude": longitude, "latitude": latitude,
                                  "horizontal_accuracy": horizontal_accuracy, "obdInfo": ODB, 'platformName': device,
                                  'platformVersion': platformVersion}

                senzor_data.append(image_data)

    except Exception:
        print ("")
        print ("An error has appeared in track.txt")
    return senzor_data


def deletePhoto(dir, photo):
    files = file(dir + 'backup_track.txt')
    read = files.readline().replace(" ", ";")
    version = read.split(';')[2].replace("\n", "")
    device = read.split(";")[0]
    if 'iP' in device:
        if version == "":
            version = 'ios_first_version'
    f = open(dir + 'index_write.txt')
    output = []
    curent_format = format[version]
    output.append(f.readline())

    for lines in f:
        line = lines.replace("\n", "")
        if "," in line:
            continue
        if line.split(";")[curent_format['index']] != photo:
            output.append(line + "\n")

    f.close()
    f = open(dir + 'backup_track.txt', 'w')
    f.writelines(output)
    f.close()


if __name__ == "__main__":
    main(sys.argv[1:])
