# Upload scripts 
Uploader tools for [OpenStreetCam](https://www.openstreetcam.org/)

# 1.Upload photos taken by OSC app

## Description:
This script is used to upload photos/videos from a local directory, that , taken with the iOS/Android OSC apps. 
The user will need to login and grant access  and after this step the script will upload automatically all photos and metadata files. 
Also will show in terminal the status for each sequence.

## Requirements:
Python 3 + dependencies from the requirements file.
The requirements can be install by running :
```
pip3 install virtualenv
virtualenv -p python3 .
source bin/activate
pip3 install -r requirements.txt
```

## Usage:

```
cd upload_osc_apps

python upload_photos.py -p /Users/example/Desktop/Photos/

python upload_video.py -p /Users/example/Desktop/Videos/

python upload_photos.py -h for help

python upload_video.py -h for help
```
Note, that upload_video.py can work on Windows. Steps for that are:
```
remove `Pillow` module from requirements.txt
pip install `virtualenv`
virtualenv -p python .
Scripts\activate.bat
pip install -r requirements.txt
Some other modules can be required depending on your installed Python distribution.
Path to file must include slash ('/') instead of backslash('\')
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

```

## Usage:
```
python upload_exif.py -p /Users/example/Desktop/Photos/AllPhotos/

python upload_exif.py -h for help.

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

find /home/bozo/mypics -mindepth 1 -type d -print0 | xargs -L 1 --null ./upload_exif.py -p

# -print0 / --null allows to read filenames with spaces, etc. in them
```

If you have installed the requirements into a `virtualenv`, then run
```
source <path to virtualenv>/bin/activate
```
before executing the above commands.

## Docker

If you have Docker, you can use these scripts without installing Python nor its requirements:
```bash
docker run -it --rm -v /where/your/images/are:/data openstreetcam/upload_photos_by_exif
docker run -it --rm -v /where/your/videos/are:/data openstreetcam/upload_osv_videos
docker run -it --rm -v /where/your/photos/are:/data openstreetcam/upload_osv_photos
```

