#!/usr/bin/env python
__author__ = "Racasan Bogdan"
# Working for and track.txt
# Working for 1.1
# Working for iOS and Android metaData file

import getopt
import gzip
import os
import requests
import cookielib
import urllib2
import sys
from rauth import OAuth1Service


def main(argv):
    try:
        read_input = raw_input
    except NameError:
        read_input = input
    try:
        opts, args = getopt.getopt(argv, "hp:r:", ["path=", "run="])
    except getopt.GetoptError:
        print ('upload_video.py -p <path>')
        sys.exit(2)
    if opts == []:
        print ('upload_video.py -p <path>')
        sys.exit()
    elif "-p" != opts[0][0] and opts[0][0] != "-h":
        print ('upload_video.py -p <path>')
        sys.exit()

    else:
        for opt, arg in opts:
            if opt == '-h':
                print ("")
                print ("Usage:")
                print ('    upload_video.py -p <path> -r <run> ')
                print ("-General Options:")
                print ("    -h                         Show help.")
                print ("    -p   --path                Full path to main directory that contains the track directories")
                print ("-Optional:")
                print ("    -r   --run                 This upload video on: http://openstreetview.com/")
                print (
                    "    -r   --run staging         This upload video on: http://staging.open-street-view.skobbler.net")
                print ("    -r   --run test            This upload video on: http://tst.open-street-view.skobbler.net/")
                print ("Example: ")
                print ("    python upload_video.py -p /Users/example/Desktop/Photos/ ")
                print ("    python upload_video.py -p /Users/example/Desktop/Photos/ -r production")
                print ("    python upload_video.py -p /Users/example/Desktop/Photos/ -r test")
                print ("    python upload_video.py -p /Users/example/Desktop/Photos/ -r staging")

                sys.exit()
            elif opt in ("-p", "--path"):
                run = 'prod'
                path = arg
            elif opt in ("-r", "--run"):
                run = arg
    try:
        id_file = open("id_file.txt", "r+")
        string = id_file.read()
        user_id = string.split(";")[0]
        user_name = string.split(";")[1]
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
        print (read_input("Login and  grant acces then press ENTER"))
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
            session = osm.get_auth_session(request_token,
                                           request_token_secret,
                                           method='POST',
                                           data={'oauth_verifier': pin})
            r = session.get('/api/0.6/user/details', verify=False)
            user_id = r.content.split("user id=")[1].split(" display_name")[0].replace('"', '')
            user_name = r.content.split("display_name=")[1].split(" account_created=")[0].replace('"', '')
            id_file = open("id_file.txt", "w+")
            id_file.write(user_id + ";")
            id_file.write(user_name)
            id_file.close()
        except Exception as ex:
            print ("ERROR LOGIN no GRANT ACCES")
            sys.exit()

    # run = "test"
    if run == "test":
        url_sequence = 'http://tst.open-street-view.skobbler.net/1.0/sequence/'
        url_video = 'http://tst.open-street-view.skobbler.net/1.0/video/'
        url_finish = 'http://tst.open-street-view.skobbler.net/1.0/sequence/finished-uploading/'
    elif run == "staging":
        url_sequence = 'http://staging.open-street-view.skobbler.net/1.0/sequence/'
        url_video = 'http://staging.open-street-view.skobbler.net/1.0/video/'
        url_finish = 'http://staging.open-street-view.skobbler.net/1.0/sequence/finished-uploading/'
    else:
        url_sequence = 'http://openstreetview.com/1.0/sequence/'
        url_video = 'http://openstreetview.com/1.0/video/'
        url_finish = 'http://openstreetview.com/1.0/sequence/finished-uploading/'

    directory = os.listdir(path)
    for dir in directory:
        dir_err = False
        if os.path.isfile(path + "/" + dir + "/track.txt") or os.path.isfile(path + "/" + dir + "/track.txt.gz"):
            print("Processing directory: " + str(dir))
            dir_path = path + "/" + dir + "/"
            if os.path.isfile(path + "/" + dir + "/track.txt"):
                metaData_name = 'track.txt'
                metaData_type = 'text/plain'
            elif os.path.isfile(path + "/" + dir + "/track.txt.gz"):
                metaData_name = 'track.txt.gz'
                metaData_type = 'gzip'
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
            backup_path = dir_path + metaData_name
            if "gz" in metaData_name:
                metaData = gzip.open(backup_path, "r")
                metaData1 = gzip.open(backup_path, "r")
            else:
                metaData = file(backup_path, "r")
                metaData1 = file(backup_path, "r")
            # create request for sequence id
            senzor_data1 = parseCsv(metaData1, backup_path)
            for video in senzor_data1:
                files = {'metaData': (metaData_name, open(dir_path + metaData_name, "rb"), metaData_type)}
                try:
                    app_version = video['app_version']
                except:
                    app_version = None
                if app_version is None:
                    if app_version is None:
                        data_sequence = {'externalUserId': user_id,
                                         'userType': 'osm',  # harcode
                                         'userName': user_name,
                                         'clientToken': '2ed202ac08ea9cf8d5f290567037dcc42ed202ac08ea9cf8d5f290567037dcc4',
                                         # harcode
                                         'currentCoordinate': str(video['latitude']) + "," + str(video['longitude']),
                                         'obdInfo': video['obdInfo'],
                                         'platformName': video['platformName'],
                                         'platformVersion': video['platformVersion']
                                         }
                    else:
                        data_sequence = {'externalUserId': user_id,
                                         'userType': 'osm',  # harcode
                                         'userName': user_name,
                                         'clientToken': '2ed202ac08ea9cf8d5f290567037dcc42ed202ac08ea9cf8d5f290567037dcc4',
                                         # harcode
                                         'currentCoordinate': str(video['latitude']) + "," + str(video['longitude']),
                                         'obdInfo': video['obdInfo'],
                                         'platformName': video['platformName'],
                                         'platformVersion': video['platformVersion'],
                                         'appVersion': video['appVersion']
                                         }

                try:
                    sequence_file = file(dir_path + "sequence_file.txt", "r+")
                    id_sequence = sequence_file.read()
                    break
                except Exception as ex:
                    sequence_file = file(dir_path + "sequence_file.txt", "w+")
                    h = requests.post(url_sequence, data=data_sequence, files=files)
                    try:
                        id_sequence = h.json()['osv']['sequence']['id']
                        sequence_file.write(id_sequence)
                        sequence_file.close()
                        break
                    except Exception as ex:
                        print ('Err sequence request')
                        os.remove(dir_path + "sequence_file.txt")
                        os.remove(dst)
                        dir_err = True
                        break

            senzor_data = parseCsv(metaData, backup_path)
            count = 0
            if not dir_err:
                for video_data in senzor_data:
                    try:
                        if firs_id_sequence < int(video_data['index']):
                            video = {'video': (
                                video_data['index'] + '.mp4', open(dir_path + video_data['index'] + '.mp4', 'rb'),
                                'video/mp4')}
                            data_video = {
                                'sequenceId': id_sequence,
                                'sequenceIndex': video_data['index']
                            }
                            try:
                                p = requests.post(url_video, data=data_video, files=video)
                            except requests.exceptions.Timeout:
                                print("Timout error  retry:")
                                count_timeout = 0
                                for i in range(0, 9):
                                    try:
                                        count_timeout += 1
                                        print("Retry : " + str(i))
                                        p = requests.post(url_video, data=data_video, files=video)
                                        if int(p.json()['osv']['video']['id']) != "":
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
                                if int(p.json()['osv']['video']['id']) != "":
                                    count += 1
                                    img_index = video_data['index']
                                    total_img = senzor_data[len(senzor_data) - 1]['index']
                                    percentage = float((float(img_index) * 100) / float(total_img))
                                    print ("Uploaded :" + img_index + '.mp4, remaining :' + str(
                                        len(senzor_data) - count) + ", percentage: " + str(round(percentage, 2)) + "%")
                                    index_write.write(str(img_index) + "\n")
                                    video['video'][1].close()
                            except Exception as ex:
                                print ("Err for: " + video_data['index'] + ".mp4 with message: " + str(
                                    p.json()['status']['apiMessage']))
                    except Exception as ex:
                        if str(ex) == "local variable 'firs_id_sequence' referenced before assignment":
                            print ("Index file is corrupted")
                            print ("The index file will be deleted and start from the first photo")
                            print ("Please restart the script")
                            os.remove(dst)
                            sys.exit()
                        print ("ERR")
                        print (ex)
                data_finish = {'externalUserId': user_id,
                               'userType': 'osm',  # harcode
                               'sequenceId': id_sequence
                               }
                f = requests.post(url_finish, data=data_finish)
                dir_err = False
                if f.json()['status']['apiCode'] == '600':
                    print ("Finish uploading form dir: " + dir_path + ' with sequence id: ' + str(id_sequence))
                else:
                    print ("FAIL uploading form dir: " + dir_path)
            else:
                print ("")


format = {
    '1.1': {'time': 0, 'compas': 13, 'videoIndex': 14, 'tripFrameIndex': 15, 'longitude': 1, 'latitude': 2,
            'horizontal_accuracy': 4, 'ODB': 19},
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
        time_longitude = 0
        time_latitude = 0
        longitude = 0
        latitude = 0
        last_index = -1
        odb_info = 0
        for line in files:
            if "," in line:
                continue
            lines = line.replace("\n", "")
            if lines == '':
                continue
            if lines.split(";")[curent_format['longitude']] != '' and time_longitude < lines.split(";")[
                curent_format['time']]:
                time_longitude = lines.split(";")[curent_format['time']]
                longitude = lines.split(";")[curent_format['longitude']]
            if lines.split(";")[curent_format['latitude']] != '' and time_latitude < lines.split(";")[
                curent_format['time']]:
                time_latitude = lines.split(";")[curent_format['time']]
                latitude = lines.split(";")[curent_format['latitude']]
            if lines.split(";")[curent_format['ODB']] != '' and time_latitude < lines.split(";")[
                curent_format['time']]:
                odb_info = 1
            if lines.split(";")[curent_format['videoIndex']] != '':
                videoIndex = lines.split(";")[curent_format['videoIndex']]
                if videoIndex != last_index:
                    last_index = videoIndex
                    video_data = {"index": videoIndex, 'latitude': latitude, 'longitude': longitude,
                                  'obdInfo': odb_info, 'platformVersion': platformVersion, 'app_version': app_version,
                                  'platformName': device}
                    senzor_data.append(video_data)

    except Exception as ex:
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
