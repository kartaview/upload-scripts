![KartaView](https://github.com/kartaview/upload-scripts/blob/master/logo-KartaView-light.png)

## KartaView Tools

##### Description
Tools developed by [KartaView](https://kartaview.org/) to help contributors.

##### Requirements
* Python 3.6+
* Dependencies from _requirements.txt_ file.
The dependencies can be installed by running:
```sh
pip3 install virtualenv

virtualenv -p python3 .

source bin/activate

pip3 install -r requirements.txt
```

## 1. Upload photos to KartaView

##### Description
This script is used to upload sequences from a local directory. The available formats are:
* Sequences taken with the OSC mobile apps
* Exif images
 
##### Usage
```sh
cd /path_to_scripts/osc_tools

# help
python osc_tools.py -h

# help for upload
python osc_tools.py upload -h

# upload all sequences from ~/OSC_sequences folder
python osc_tools.py upload -p ~/OSC_seqences

```

## 2. Generate Exif info 

##### Description
This script generates GPS Exif for each image. It has two options generating exif info from metadata file or generating exif info from a custom geojson file. 

```sh
cd /path_to_scripts

# help
python osc_tools.py -h

# help for Exif generation
python osc_tools.py generate_exif -h
```

#### Option I. From an KV metadata format file
```sh
# Exif generation for mobile recorded sequence having metadata files in ~/OSC_sequences/Sequence1 folder
python osc_tools.py generate_exif -exif_source metadata -p ~/OSC_seqences/Sequence1

```

#### Option II. From custom geojson file and the images that require the exif data

```sh
# Exif generation for custom geojson + imagery 
python osc_tools.py generate_exif -exif_source custom_geojson -p ~/CustomFolderContainingGeoJsonAndImages

```
<details>
 <summary>Folder structure</summary>

```
 ~/CustomFolderContainingGeoJsonAndImages
 ~/CustomFolderContainingGeoJsonAndImages/a_file.geojson
 ~/CustomFolderContainingGeoJsonAndImages/folder_with_images
 ~/CustomFolderContainingGeoJsonAndImages/folder_with_images/image1.jpg
 ~/CustomFolderContainingGeoJsonAndImages/folder_with_images/image2.jpg
 ~/CustomFolderContainingGeoJsonAndImages/folder_with_images/image3.jpg
```
</details>


<details>
  <summary>Expand to see the custom geojson sample:</summary>
 
  ```json
  {
      "type": "FeatureCollection",
      "features": [
      {
          "type": "Feature",
          "properties": {
              "order": 1,
              "path": "folder_with_images/image1.jpg",
              "direction": 236.0,
              "Lat": 1.910309,
              "Lon": 1.503069,
              "Timestamp": "2020-01-20T08:00:01Z"
          },
          "geometry": { 
              "type": "Point",
              "coordinates": [ 1.503069408072847, 1.910308570011793 ]
          }
      },
      {
          "type": "Feature",
          "properties": {
              "order": 2,
              "path": "folder_with_images/image2.jpg",
              "direction": 236.0,
              "Lat": 1.910199,
              "Lon": 1.502908,
              "Timestamp": "2020-01-20T08:01:21Z"
          },
          "geometry": {
              "type": "Point",
              "coordinates": [ 1.502907515952158, 1.910198963742701 ]
          }
      },
      {
          "type": "Feature",
          "properties": {
              "order": 3,
              "path": "folder_with_images/image3.jpg",
              "direction": 236.0,
              "Lat": 1.910096,
              "Lon": 1.502764,
              "Timestamp": "2020-01-20T08:12:10Z"
          },
          "geometry": {
              "type": "Point",
              "coordinates": [ 1.50276400212099, 1.910095961756973 ]
          }
      }
      ]   
  }
  ```
  | Member | Type | Format | Comment |
  | ------ | ---- | ------ | ------- |
  | `Timestamp` | string | `%Y-%m-%dT%H:%M:%SZ` | [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339), not full ISO 8601 |
  | `Lat` | float | `-90.0` <= `Lat` <= `90.0` | latitude in decimal degrees |
  | `Lng` | float | `0.0` <= `Lng` < `360.0`| longitude in decimal degrees |
  | `order` | int | `order` >= `1` | order of image in the track |
  | `direction` | float | `0.0` <= `direction` < `360.0` | cardinal direction in degrees the image was taken |
  | `path` | string | operating system’s specific path format | image path relative to the geojson file |
</details>


### Docker Support
To run the scripts inside a Docker container:
```sh
make docker
docker run -Pit osc-up osc_tools.py
docker run -Pit --mount type=bind,source="$(pwd)",target=/opt/osc osc-up /opt/osc/osc_tools.py
```
The 'images' directory in the repo will be available in the container at /opt/osc/images
