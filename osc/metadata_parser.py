format = {
    'ios_first_version': {'time': 0, 'compas': 1, 'index': 13, 'longitude': 1, 'latitude': 2,
                          'horizontal_accuracy': 4},
    '1.0.3': {'time': 0, 'compas': 12, 'index': 13, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4},
    '1.0.5': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4},
    '1.0.6': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4,
              'ODB': 18},
    '1.0.7': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4,
              'ODB': 18},
    '1.0.8': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4,
              'ODB': 18},
    '1.1': {'time': 0, 'compas': 13, 'videoIndex': 14, 'tripFrameIndex': 15, 'longitude': 1, 'latitude': 2,
            'horizontal_accuracy': 4, 'ODB': 19},
    '1.1.1': {'time': 0, 'compas': 13, 'videoIndex': 14, 'tripFrameIndex': 15, 'longitude': 1, 'latitude': 2,
              'horizontal_accuracy': 4, 'ODB': 19},
    '1.1.2': {'time': 0, 'compas': 13, 'videoIndex': 14, 'tripFrameIndex': 15, 'longitude': 1, 'latitude': 2,
              'horizontal_accuracy': 4, 'ODB': 19},
    '1.1.3': {'time': 0, 'compas': 13, 'videoIndex': 14, 'tripFrameIndex': 15, 'longitude': 1, 'latitude': 2,
              'horizontal_accuracy': 4, 'ODB': 19},
    '1.1.5': {'time': 0, 'compas': 13, 'videoIndex': 14, 'tripFrameIndex': 15, 'longitude': 1, 'latitude': 2,
              'horizontal_accuracy': 4, 'ODB': 19},
    '1.1.6': {'time': 0, 'compas': 13, 'videoIndex': 14, 'tripFrameIndex': 15, 'index': 15, 'longitude': 1, 'latitude': 2,
              'horizontal_accuracy': 4, 'ODB': 19}
}


def get_app_details(files):
    read = str(files.readline()).replace(" ", "_")
    read = read.split(";")
    device = read[0].replace('_', ' ')
    app_version = None
    if 'iP' in device:
        version = read[2].replace("\n", "")
        if version == "":
            version = 'ios_first_version'
            platform_version = 'Unknown'
        else:
            try:
                platform_version = read[1].replace("\n", "")
            except Exception:
                platform_version = 'Unknown'
            if version == '1.0.8':
                app_version = read[3].replace("\n", "")
    else:
        version = read[2].replace("\n", "")
        if version == "":
            version = 'ios_first_version'
            platform_version = 'Unknown'
        else:
            try:
                platform_version = read[1].replace("\n", "")
            except Exception:
                platform_version = 'Unknown'
            if version == '1.0.8':
                app_version = read[3].replace("\n", "")
    return version, app_version, platform_version, device


def process_video_meta(files, current_format, platform_version, device, app_version):
    sensor_data = []
    time_longitude = 0
    time_latitude = 0
    longitude = 0
    latitude = 0
    last_index = -1
    odb_info = 0
    try:
        for line in files:
            if "," in line or line == '' or str(line) == 'DONE':
                continue
            lines = line.replace("\n", "").split(';')
            if lines[current_format['longitude']] != '' and str(time_longitude) < lines[current_format['time']]:
                time_longitude = lines[current_format['time']]
                longitude = lines[current_format['longitude']]
            if lines[current_format['latitude']] != '' and str(time_latitude) < lines[current_format['time']]:
                time_latitude = lines[current_format['time']]
                latitude = lines[current_format['latitude']]
            if lines[current_format['ODB']] != '' and str(time_latitude) < lines[current_format['time']]:
                odb_info = 1
            if lines[current_format['videoIndex']] != '':
                video_index = lines[current_format['videoIndex']]
                if video_index != last_index:
                    last_index = video_index
                    video_data = {"index": video_index, 'latitude': latitude, 'longitude': longitude,
                                  'obdInfo': odb_info, 'platformVersion': platform_version, 'app_version': app_version,
                                  'platformName': device}
                    sensor_data.append(video_data)
    except:
        print("")
        print("An error has appeared in track.txt")
        return sensor_data
    return sensor_data


def process_photo_meta(files, current_format, platform_version, device, app_version, version):
    compass = -1
    longitude = 0
    latitude = 0
    horizontal_accuracy = 0
    obd = 0
    time_compass = 0
    time_longitude = 0
    time_latitude = 0
    time_horizontal_accuracy = 0
    sensor_data = []
    try:
        for line in files:
            line = str(line)
            if "," in line or line == '' or 'DONE' in str(line):
                continue
            lines = line.replace("\n", "").split(';')
            if lines[current_format['compas']] != '' and str(time_compass) < lines[current_format['time']]:
                time_compass = lines[current_format['time']]
                compass = lines[current_format['compas']]
            if lines[current_format['longitude']] != '' and str(time_longitude) < lines[current_format['time']]:
                time_longitude = lines[current_format['time']]
                longitude = lines[current_format['longitude']]
            if lines[current_format['latitude']] != '' and str(time_latitude) < lines[current_format['time']]:
                time_latitude = lines[current_format['time']]
                latitude = lines[current_format['latitude']]
            if lines[current_format['horizontal_accuracy']] != '' and str(time_horizontal_accuracy) < lines[current_format['time']]:
                time_horizontal_accuracy = lines[current_format['time']]
                horizontal_accuracy = lines[current_format['horizontal_accuracy']]
            try:
                if lines[current_format['ODB']] != '':
                    obd = 1
            except:
                pass
            if lines[current_format['index']] != '':
                index = lines[current_format['index']]
                if version == 'ios_first_version':
                    compass = ''
                if app_version is not None:
                    image_data = {"index": index, "compas": compass, "longitude": longitude, "latitude": latitude,
                                  "horizontal_accuracy": horizontal_accuracy, "obdInfo": obd, 'platformName': device,
                                  'platformVersion': platform_version,
                                  'appVersion': app_version}
                else:
                    image_data = {"index": index, "compas": compass, "longitude": longitude, "latitude": latitude,
                                  "horizontal_accuracy": horizontal_accuracy, "obdInfo": obd, 'platformName': device,
                                  'platformVersion': platform_version}

                sensor_data.append(image_data)
    except Exception as ex:
        print(ex)
        print("An error has appeared in track.txt")
        return sensor_data
    return sensor_data


def parse_csv(files, type_upload):
    sensor_data = []
    try:
        version, app_version, platform_version, device = get_app_details(files)
        current_format = format[version]
        if type_upload == 'video':
            sensor_data = process_video_meta(files, current_format, platform_version, device, app_version)
        else:
            sensor_data = process_photo_meta(files, current_format, platform_version, device, app_version, version)
    except Exception as ex:
        print("Error metadata: {}".format(ex))
        print("An error has appeared in track.txt")
    return sensor_data
