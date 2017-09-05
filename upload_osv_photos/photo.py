from tqdm import tqdm
from osc.osc_actions import make_request
from osc.utils import write_result, exception_firs_id_sequence


def get_data_photo(image_data, access_token, id_sequence, count):
    if image_data['compas'] != '':
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
    return data_photo


def upload_photos(url_photo, sensor_data, dir_path, firs_id_sequence, access_token, id_sequence, index_write):
    count = 0
    for index_sensor in tqdm(range(0, len(sensor_data)),
                             bar_format='{l_bar}{bar} {n_fmt}/{total_fmt} remaining:{remaining}  elapsed:{elapsed}'):
        try:
            image_data = sensor_data[index_sensor]
            if firs_id_sequence < int(image_data['index']):
                photo = {'photo': (
                    image_data['index'] + '.jpg', open(dir_path + '/' + image_data['index'] + '.jpg', 'rb'),
                    'image/jpeg')}
                data_photo = get_data_photo(image_data, access_token, id_sequence, int(image_data['index']))
                response = make_request(url_photo, data_photo, photo, 'photo')
                if response == 660:
                    continue
                write_result(response, index_write, image_data)
        except Exception as ex:
            exception_firs_id_sequence(ex, index_write)
            print("ERR")
