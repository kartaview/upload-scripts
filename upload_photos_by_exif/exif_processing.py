from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def get_exif(path):
    import exifread
    with open(path, 'rb') as fh:
        tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
        date_taken = tags["EXIF DateTimeOriginal"]
        return date_taken


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
    except:
        pass
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
        exif_data_gps_info = exif_data.get('GPSInfo')
        if not exif_data_gps_info:
            raise ValueError("No GPS metadata found.")
        try:
            lat = exif_data_gps_info['GPSLatitude']
        except:
            pass
        try:
            long = exif_data_gps_info['GPSLongitude']
        except:
            pass

        try:
            if lat and int:
                lat = (float(lat[0][0]) / float(lat[0][1]) + float(lat[1][0]) / float(lat[1][1]) / 60.0 + float(
                    lat[2][0]) / float(lat[2][1]) / 3600.0)
                long = (
                    float(long[0][0]) / float(long[0][1]) + float(long[1][0]) / float(long[1][1]) / 60.0 + float(
                        long[2][0]) / float(long[2][1]) / 3600.0)
            if exif_data_gps_info['GPSLatitudeRef'] == 'S':
                lat = 0 - lat
            if exif_data_gps_info['GPSLongitudeRef'] == 'W':
                long = 0 - long
        except Exception as ex:
            pass
        try:
            compas = exif_data_gps_info['GPSImgDirection']
            compas = compas[0] / compas[1]
        except Exception:
            try:
                compas = exif_data_gps_info['GPSTrack']
                compas = compas[0] / compas[1]
            except Exception:
                compas = -1
        return lat, long, compas


