"""Module responsible to parse Exif information from a image"""
from typing import Optional, List, Type
import gpxpy.gpx
from datetime import datetime

from parsers.base import BaseParser
from common.models import SensorItem, GPS


class GPXParser(BaseParser):
    """this class is a BaseParser that can parse a GPX"""

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        if item_class != GPS:
            return None
        with self._storage.open(self.file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            index = 0
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if index == self._data_pointer:
                            gps = GPS()
                            gps.speed = point.speed
                            gps.timestamp = point.time.timestamp()
                            gps.latitude = point.latitude
                            gps.longitude = point.longitude
                            gps.altitude = point.elevation
                            self._data_pointer += 1
                            return gps
        return None

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        if item_class != GPS:
            return []
        with open(self.file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            sensors: List[SensorItem] = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        gps = GPS()
                        gps.speed = point.speed
                        gps.timestamp = point.time.timestamp()
                        gps.latitude = point.latitude
                        gps.longitude = point.longitude
                        gps.altitude = point.elevation
                        sensors.append(gps)
            return sensors

    def next_item(self) -> Optional[SensorItem]:
        with open(self.file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            index = 0
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if index == self._data_pointer:
                            gps = GPS()
                            gps.speed = point.speed
                            gps.timestamp = point.time.timestamp()
                            gps.latitude = point.latitude
                            gps.longitude = point.longitude
                            gps.altitude = point.elevation
                            self._data_pointer += 1
                            return gps
        return None

    def items(self) -> List[SensorItem]:
        with open(self.file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            sensors: List[SensorItem] = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        gps = GPS()
                        gps.speed = point.speed
                        gps.timestamp = point.time.timestamp()
                        gps.latitude = point.latitude
                        gps.longitude = point.longitude
                        gps.altitude = point.elevation
                        sensors.append(gps)
            return sensors

    def format_version(self) -> Optional[str]:
        with open(self.file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            return gpx.version

    def serialize(self):
        my_gpx = gpxpy.gpx.GPX()
        # Create first track in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        my_gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        for item in self._sensors:
            if isinstance(item, GPS):
                gpx_segment.points.append(self._gpx_track_point(item))
            # elif isinstance(item, PhotoMetadata):
            #     gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=item.gps.latitude,
            #                                                       longitude=item.gps.longitude,
            #                                                       elevation=item.gps.altitude,
            #                                                       time=item.gps.timestamp,
            #                                                       speed=item.gps.speed))
        xml_data = my_gpx.to_xml()
        with open(self.file_path, "w+") as file:
            file.write(xml_data)
        file.close()

    @classmethod
    def _gpx_track_point(cls, item: GPS) -> Optional[gpxpy.gpx.GPXTrackPoint]:
        point = None
        if item.timestamp is None:
            return None

        item.timestamp += 1526814822
        if item.latitude and item.longitude and item.timestamp:
            time = datetime.fromtimestamp(float(item.timestamp))
            point = gpxpy.gpx.GPXTrackPoint(latitude=float(item.latitude),
                                            longitude=float(item.longitude),
                                            time=time)
        if point and item.speed:
            point.speed = float(item.speed)

        if point and item.altitude:
            point.elevation = float(item.altitude)

        return point

    def compatible_sensors(self):
        return [GPS]
