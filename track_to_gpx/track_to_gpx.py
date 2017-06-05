import getopt
import gzip
import os
import sys
import traceback
import time
from string import Template

__author__ = "Mark Prins"

gpxHeader = Template("""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1"
     creator="OSC track_to_gpx"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:osc="http://www.openstreetcam.org/GPX/1/1"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <trk>
    <name>$seq</name>
    <desc>OSC tracklog data sequence $seq</desc>
    <src>$src</src>
    <number>1</number>
    <trkseg>""")

trkPoint = Template("""
      <trkpt lat="$latitude" lon="$longitude">
        <ele>$ele</ele>
        <time>$time</time>
        <name>picture $index</name>
        <cmt>$index</cmt>
        <pdop>$horizontal_accuracy</pdop>
        <extensions>
          <osc:speed>$speed</osc:speed>
          <osc:bearing>$compas</osc:bearing>
          <osc:obd>$obdInfo</osc:obd>
      </extensions>
      </trkpt>""")

gpxFooter = """
    </trkseg>
  </trk>
</gpx>"""

format = {
          '1.0.3': {'time': 0, 'compas': 12, 'index': 13, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4},
          '1.0.5': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4},
          '1.0.6': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4, 'ODB': 18},
          '1.0.7': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4, 'ODB': 18},
          '1.0.8': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4, 'ODB': 18},
          'ios_first_version': {'time': 0, 'compas': 1, 'index': 13, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4},
          '1.1.6': {'time': 0, 'compas': 13, 'index': 14, 'longitude': 1, 'latitude': 2, 'horizontal_accuracy': 4, 'ODB': 18},
         }

def main(argv):
    try:
        read_input = raw_input
    except NameError:
        read_input = input
    try:
        opts, args = getopt.getopt(argv, "hp:")
    except getopt.GetoptError:
        print ('track_to_gpx.py -p <path>')
        sys.exit(2)
    if opts == []:
        print ('track_to_gpx.py -p <path>')
        sys.exit(2)
    elif "-p" != opts[0][0] and opts[0][0] != "-h":
        print ('track_to_gpx.py -p <path>')
        sys.exit(2)
    else:
        for opt,arg in opts:
            if opt == '-h':
                print ("")
                print ("Usage:")
                print ('    track_to_gpx.py -p <path>')
                print ("-General Options:")
                print ("    -h                         Show help.")
                print ("    -p                         Full path to main directory that contains the track directories")
                print ("Example: ")
                print ("    python track_to_gpx.py -p /Users/example/Desktop/Photos/ ")
                sys.exit()
            elif opt == "-p":
                createGPX(arg)

def createGPX(path):
    directory = os.listdir(path)
    for dir in directory:
        if os.path.isfile(path + "/" + dir + "/track.txt") or os.path.isfile(path + "/" + dir + "/track.txt.gz"):
            print("Processing directory: " + str(dir))
            dir_path = path + "/" + dir + "/"
            if os.path.isfile(path + "/" + dir + "/track.txt"):
                metaData_name = 'track.txt'
                metadata_path = dir_path + metaData_name
            elif os.path.isfile(path + "/" + dir + "/track.txt.gz"):
                metaData_name = 'track.txt.gz'
                metadata_path = dir_path + metaData_name

            if "gz" in metaData_name:
                metaData = gzip.open(metadata_path, "r")
            else:
                metaData = file(metadata_path, "r")

            senzor_data, src = parseCsv(metaData)

            # create gpx and add header
            gpx = file(path + "/" + dir + "/track.gpx", "w+")
            gpx.write(gpxHeader.substitute(seq=dir, src=src))

            for image in senzor_data:
                gpx.write(trkPoint.substitute(image))

            gpx.write(gpxFooter)
            gpx.close()

def parseCsv(files):
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
        speed = ''
        ele = 0
        horizontal_accuracy = 0
        ODB = 0
        time_compas = 0
        time_longitude = 0
        time_latitude = 0
        time_horizontal_accuracy = 0
        _time = 0
        index = -1
        for line in files:
            if "," in line:
                continue
            lines = line.replace("\n", "")
            if lines.split(";")[curent_format['compas']] != '' and time_compas < lines.split(";")[
                curent_format['time']]:
                _time = lines.split(";")[curent_format['time']]
                time_compas = lines.split(";")[curent_format['time']]
                compas = lines.split(";")[curent_format['compas']]
            if lines.split(";")[curent_format['longitude']] != '' and time_longitude < lines.split(";")[
                curent_format['time']]:
                _time = lines.split(";")[curent_format['time']]
                time_longitude = lines.split(";")[curent_format['time']]
                longitude = lines.split(";")[curent_format['longitude']]
            if lines.split(";")[curent_format['latitude']] != '' and time_latitude < lines.split(";")[
                curent_format['time']]:
                _time = lines.split(";")[curent_format['time']]
                time_latitude = lines.split(";")[curent_format['time']]
                latitude = lines.split(";")[curent_format['latitude']]
            if lines.split(";")[curent_format['horizontal_accuracy']] != '' and time_horizontal_accuracy < \
                    lines.split(";")[curent_format['time']]:
                _time = lines.split(";")[curent_format['time']]
                time_horizontal_accuracy = lines.split(";")[curent_format['time']]
                horizontal_accuracy = lines.split(";")[curent_format['horizontal_accuracy']]
            try:
                if lines.split(";")[curent_format['ODB']] != '':
                    ODB = 1
            except Exception as ex:
                ex
            if lines.split(";")[curent_format['index']] != '':
                # index = lines.split(";")[curent_format['index']]
                if version == 'ios_first_version':
                    compas = '-1'
                index += 1
                image_data = {
                              "index": index,
                              "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(_time))),
                              "compas": compas,
                              "longitude": longitude,
                              "latitude": latitude,
                              "horizontal_accuracy": horizontal_accuracy,
                              "obdInfo": ODB,
                              "speed" : speed,
                              "ele" : ele
                             }

                senzor_data.append(image_data)

    except Exception, err:
        print ("")
        print ("An error occurred processing track.txt")
        traceback.print_exc()
    return senzor_data, "Device: " + device + ", OS version: "+ platformVersion +" running OpenStreetCam version: " + version


if __name__ == "__main__":
    main(sys.argv[1:])
