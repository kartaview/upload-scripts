from tqdm import tqdm
from osc.osc_actions import make_request
from osc.utils import exception_firs_id_sequence, write_result


def upload_videos(url_video, sensor_data, dir_path, firs_id_sequence, access_token, id_sequence, index_write):
    count = 0
    for index_sensor in tqdm(range(0, len(sensor_data)),
                             bar_format='{l_bar}{bar} {n_fmt}/{total_fmt} remaining:{remaining}  elapsed:{elapsed}'):
        video_data = sensor_data[index_sensor]
        try:
            if firs_id_sequence < int(video_data['index']):
                video = {'video': (
                    video_data['index'] + '.mp4', open(dir_path + '/' + video_data['index'] + '.mp4', 'rb'),
                    'video/mp4')}
                data_video = {'access_token': access_token,
                              'sequenceId': id_sequence,
                              'sequenceIndex': video_data['index']
                              }
                response = make_request(url_video, data_video, video, 'video')
                if response == 660:
                    continue
                write_result(response, index_write, video_data)
        except Exception as ex:
            exception_firs_id_sequence(ex, index_write)
            print(ex)
