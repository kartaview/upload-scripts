# Upload scripts
Uploader tools for OpenStreetView

# 1.Upload photos taken by OSV app

## Description:
This script is used to upload photos from a local directory, taken with the iOS/Android OSV apps.
The user will need to login and grant access  and after this step the script will upload automatically all photos and metadata files.
Also will show in terminal the status for each sequence.

## Requirements:
Python 2.7 + dependencies from the requirements file.
The requirements can be install by running : pip install -r requirements.txt

## Usage:

```
python upload_photos.py -p /Users/example/Desktop/Photos/

python upload_video.py -p /Users/example/Desktop/Videos/

python upload_photos.py -h for help

python upload_video.py -h for help
```
---------
# 2.Upload geotagged photos

## Description:
This script is used to upload photos from a local directory.
The user will need to login and grant access  and after this step the script will upload automatically all photos.
Also will show in terminal the status for each that directory.

## Requirements:
Python 3 + dependencies from the requirements file.
The requirements can be install by running :pip3 install -r requirements.txt

### Installing requirements on Debian/Ubuntu in a `virtualenv`

```
cd upload_photos_by_exif
apt-get install build-essential libjpeg-dev zlib1g-dev python3-pip virtualenv libpython3-dev
virtualenv -p python3 .
source bin/activate
pip install -r requirements.txt
```

## Usage:
```
python upload_photos_by_exif.py -p /Users/example/Desktop/Photos/AllPhotos/

python upload_photos_by_exif.py -h for help.

```

## Usage for uploading multiple sequences at once:

```bash
# List directories to be uploaded as sequences:

find /home/bozo/mypics -mindepth 1 -type d

# should return
#/home/bozo/mypics/a
#/home/bozo/mypics/b
#/home/bozo/mypics/c

# Upload the sequences:

find /home/bozo/mypics -mindepth 1 -type d -print0 | xargs -L 1 --null ./upload_photos_by_exif.py -p

# -print0 / --null allows to read filenames with spaces, etc. in them
```

If you have installed the requirements into a `virtualenv`, then run
```
source <path to virtualenv>/bin/activate
```
before executing the above commands.


# 3. convert track to gpx

## Description:
This script is can be used to transform the track metedata file to gpx which may then be used to add geotags to the pictures you've taken with the app.

## Requirements:
Python 2.7 +

## Usage:

```
python track_to_gpx.py -p /Users/example/Desktop/Photos/
```
