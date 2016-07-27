# uploader
Uploader tools for OpenStreetView
1.Upload photos taken by OSV app
Description:
  This script is used to upload photos from a local directory, taken with the iOS/Android OSV apps. 
  The user will need to login and grant access  and after this step the script will upload automatically all photos and metadata files. 
  Also will show in terminal the status for each sequence.
Requirements: 
    Python 2.7 + dependencies from the requirements file. 
    The requirements can be install by running : pip install -r requirements.txt
Run the upload_photos.py/upload_video.py script. 
Use -h for help.
Usage:
    python upload_photos.py -p /Users/example/Desktop/Photos/
    python upload_video.py -p /Users/example/Desktop/Videos/
    
2.Upload geotagged photos
Description:
  This script is used to upload photos from a local directory. 
  The user will need to login and grant access  and after this step the script will upload automatically all photos. 
  Also will show in terminal the status for each that directory.
Requirements: 
    Python 3 + dependencies from the requirements file. 
    The requirements can be install by running :pip3 install -r requirements.txt
Run the upload_photos_by_exif.py script. 
Use -h for help.
Usage:
    python upload_photos_by_exif.py -p /Users/example/Desktop/Photos/AllPhotos/