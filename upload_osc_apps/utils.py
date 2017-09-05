def get_data_photo(image_data, access_token, id_sequence, count, dir_path):
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
    photo = {'photo': (
        image_data['index'] + '.jpg', open(dir_path + '/' + image_data['index'] + '.jpg', 'rb'),
        'image/jpeg')}
    return data_photo, photo


def get_data_video(video_data, access_token, id_sequence, dir_path):
    data_video = {'access_token': access_token,
                  'sequenceId': id_sequence,
                  'sequenceIndex': video_data['index']
                  }
    video = {'video': (
        video_data['index'] + '.mp4', open(dir_path + '/' + video_data['index'] + '.mp4', 'rb'),
        'video/mp4')}
    return data_video, video
