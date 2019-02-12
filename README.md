![OSC](http://openstreetcam.org/assets/images/osc-logo.png)

## OSC Tools

##### Description
Tools developed by [OpenStreetCam](https://openstreetcam.org/) to help contributors.

##### Requirements
* Python 3  
* Dependencies from _requirements.txt_ file.
The dependencies can be installed by running:
```
pip3 install virtualenv

virtualenv -p python3 .

source bin/activate

pip3 install -r requirements.txt
```

##1. Upload photos to OpenStreetCam

##### Description
This script is used to upload sequences from a local directory. The available formats are:
* Sequences taken with the OSC mobile apps
* Exif images
 
##### Usage
```
cd /path_to_scripts/osc_tools

# help
python osc_tools.py -h

# help for upload
python osc_tools.py upload -h

# upload all sequences from ~/OSC_sequences folder
python osc_tools.py upload -p ~/OSC_seqences

```

##2. Generate Exif info from OSC metadata file

##### Description
This script generates GPS Exif info for each image from an OSC metadata format file.

##### Usage
```
cd /path_to_scripts

# help
python osc_tools.py -h

# help for Exif generation
python osc_tools.py generate_exif -h

# Exif generation for sequence in ~/OSC_sequences/Sequence1 folder
python osc_tools.py generate_exif -p ~/OSC_seqences/Sequence1

```
