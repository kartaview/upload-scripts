"""
This module is used to read XMP data from images.
"""
import struct
from typing import Optional, Tuple, List, Any, Type
from xml.etree.ElementTree import fromstring, ParseError

from io_storage.storage import Storage
from parsers.base import BaseParser
from common.models import SensorItem, CameraParameters, projection_type_from_name, ExifParameters


class XMPParser(BaseParser):
    """xmp parser for xmp image header"""

    def __init__(self, file_path: str, storage: Storage):
        super().__init__(file_path, storage)
        self._data_pointer = 0
        self._body_pointer = 0
        self.xmp_str = self._read_xmp()

    def _read_xmp(self) -> str:
        with self._storage.open(self.file_path, "rb") as image:
            data = image.read()
            xmp_start = data.find(b'<x:xmpmeta')
            xmp_end = data.find(b'</x:xmpmeta')
            xmp_str = data[xmp_start:xmp_end + 12]
            print("xmp end :", xmp_start, xmp_end, "\n")
            print(xmp_str)
        return xmp_str

    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        if item_class == CameraParameters:
            return self._camera_item()
        return None

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        next_item = self.next_item_with_class(item_class)
        if next_item is not None:
            return [next_item]
        return []

    def next_item(self) -> Optional[SensorItem]:
        if self._data_pointer == 0:
            self._data_pointer = 1
        return self._camera_item()

    def items(self) -> List[SensorItem]:
        camera = self._camera_item()
        if camera is not None:
            return [camera]
        return []

    def format_version(self) -> Optional[str]:
        raise NotImplementedError(f"XMP format version - {self}")

    @classmethod
    def compatible_sensors(cls) -> List[Any]:
        return [CameraParameters]

    def _camera_item(self) -> Optional[CameraParameters]:
        try:
            projection = None
            full_pano_image_width = None

            # cropped_area_image_height_pixels = None
            cropped_area_image_width_pixels = None

            root = fromstring(self.xmp_str)
            for element in root.findall("*"):
                for rdf in element.findall("*"):
                    [full_pano_image_width, cropped_area_image_width_pixels,
                     projection] = self.compute_camera_items(rdf)

                    if cropped_area_image_width_pixels is not None \
                            and full_pano_image_width is not None \
                            and projection is not None:
                        break

                    [full_pano_image_width, cropped_area_image_width_pixels,
                     projection] = self.compute_camera_items_for_garmin(rdf)

            if cropped_area_image_width_pixels is not None \
                    and full_pano_image_width is not None \
                    and projection is not None:
                parameters = CameraParameters()
                parameters.h_fov = cropped_area_image_width_pixels * 360 / full_pano_image_width
                parameters.projection = projection_type_from_name(projection)
                return parameters
            return None
        except ParseError:
            return None

    @staticmethod
    def compute_camera_items(xml_tags) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        full_pano_image_width, cropped_area_image_width_pixels, projection = (None, None, None)
        for attr_name, attr_value in xml_tags.items():
            if "FullPanoWidthPixels" in attr_name:
                full_pano_image_width = int(attr_value)
            if "CroppedAreaImageWidthPixels" in attr_name:
                cropped_area_image_width_pixels = int(attr_value)
            if "ProjectionType" in attr_name:
                projection = attr_value

        return full_pano_image_width, cropped_area_image_width_pixels, projection

    @staticmethod
    def compute_camera_items_for_garmin(xml_elements) -> Tuple[Optional[int],
                                                               Optional[int],
                                                               Optional[str]]:
        full_pano_image_width, cropped_area_image_width_pixels, projection = (None, None, None)
        for xml_child in xml_elements.findall("*"):
            if "FullPanoWidthPixels" in xml_child.tag:
                full_pano_image_width = int(xml_child.text)
            if "CroppedAreaImageWidthPixels" in xml_child.tag:
                cropped_area_image_width_pixels = int(xml_child.text)
            if "ProjectionType" in xml_child.tag:
                projection = xml_child.text

        return full_pano_image_width, cropped_area_image_width_pixels, projection

    def serialize(self):
        with self._storage.open(self.file_path, "rb") as image:
            data = image.read()
            start = data.find(b'\xff\xe1')
            for item in self._sensors:
                if isinstance(item, ExifParameters):
                    height = item.height
                    width = item.width
                    # print(str(hex_val) + xmp_header)
            xmp_header = '''<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.1.0-jc003">\n<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n<rdf:Description rdf:about="" xmlns:GPano="http://ns.google.com/photos/1.0/panorama/">\n<GPano:UsePanoramaViewer>True</GPano:UsePanoramaViewer>\n<GPano:ProjectionType>equirectangular</GPano:ProjectionType>\n<GPano:PoseHeadingDegrees>0.0</GPano:PoseHeadingDegrees>\n<GPano:PosePitchDegrees>0.0</GPano:PosePitchDegrees>\n<GPano:PoseRollDegrees>0.0</GPano:PoseRollDegrees>\n<GPano:InitialViewHeadingDegrees>0.0</GPano:InitialViewHeadingDegrees>\n<GPano:InitialViewPitchDegrees>0.0</GPano:InitialViewPitchDegrees>\n<GPano:InitialViewRollDegrees>0.0</GPano:InitialViewRollDegrees>\n<GPano:InitialHorizontalFOVDegrees>0.0</GPano:InitialHorizontalFOVDegrees>\n<GPano:InitialVerticalFOVDegrees>0.0</GPano:InitialVerticalFOVDegrees>\n<GPano:CroppedAreaLeftPixels>0</GPano:CroppedAreaLeftPixels>\n<GPano:CroppedAreaTopPixels>0</GPano:CroppedAreaTopPixels>\n<GPano:CroppedAreaImageWidthPixels>{imagewidth}</GPano:CroppedAreaImageWidthPixels>\n<GPano:CroppedAreaImageHeightPixels>{imageheight}</GPano:CroppedAreaImageHeightPixels>\n<GPano:FullPanoWidthPixels>{imagewidth}</GPano:FullPanoWidthPixels>\n<GPano:FullPanoHeightPixels>{imageheight}</GPano:FullPanoHeightPixels>\n</rdf:Description>\n</rdf:RDF>\n</x:xmpmeta>'''.format(imageheight=height, imagewidth=width)
            string_len = len(xmp_header.encode('utf-8')) + 2
            xmp_header = b'\xff\xe1' + struct.pack('>h', string_len) + xmp_header.encode('utf-8')
            if start == -1:
                with self._storage.open(self.file_path, "wb") as out_image:
                    out_image.write(data[:2] + xmp_header + data[2:])
            elif len(self.xmp_str) > 0:
                NotImplementedError("Adding information to existing XMP header is currently "
                                    "not supported")
            else:
                with self._storage.open(self.file_path, "wb") as out_image:
                    out_image.write(data[:start] + xmp_header + data[start:])
