import requests
import sys


def make_request(url_upload, post_data, files, type_upload):
    response = None
    try:
        response = requests.post(url_upload, data=post_data, files=files)
        if int(response.status_code) != 200:
            try:
                if response.json()['status']['apiCode'] == '660':
                    return 660
            except:
                return 660
            retry_count = 0
            while int(response.status_code) != 200:
                print("Retry attempt : " + str(retry_count))
                response = requests.post(url_upload, data=post_data, files=files)
                retry_count += 1
                if retry_count == 10:
                    sys.exit("Restart the script")
    except requests.exceptions.Timeout:
        print("Timeout error  retry:")
        count_timeout = 0
        for i in range(0, 9):
            try:
                count_timeout += 1
                print("Retry : " + str(i))
                response = requests.post(url_upload, data=post_data, files=files)
                if int(response.json()['osv'][type_upload]['id']) != "":
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
    return response

def get_osc_login(url_access, osm, request_token, request_token_secret, pin):
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
        print(ex)
        print("ERROR LOGIN no GRANT ACCESS")
        sys.exit()


def get_osc_url(run, type_upload):
    if run == "test":
        url_sequence = 'https://testing.openstreetcam.org/1.0/sequence/'
        url_type = 'https://testing.openstreetcam.org/1.0/{}/'.format(type_upload)
        url_finish = 'https://testing.openstreetcam.org/1.0/sequence/finished-uploading/'
        url_access = 'https://testing.openstreetcam.org/auth/openstreetmap/client_auth'
    elif run == "staging":
        url_sequence = 'https://staging.openstreetcam.org/1.0/sequence/'
        url_type = 'https://staging.openstreetcam.org/1.0/{}/'.format(type_upload)
        url_finish = 'https://staging.openstreetcam.org/1.0/sequence/finished-uploading/'
        url_access = 'https://staging.openstreetcam.org/auth/openstreetmap/client_auth'
    else:
        url_sequence = 'https://openstreetcam.org/1.0/sequence/'
        url_type = 'https://openstreetcam.org/1.0/{}/'.format(type_upload)
        url_finish = 'https://openstreetcam.org/1.0/sequence/finished-uploading/'
        url_access = 'https://openstreetcam.org/auth/openstreetmap/client_auth'
    return url_sequence, url_type, url_finish, url_access


def finish_upload(url_finish, path, access_token, id_sequence):
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
