"""This file contains parsers for osc metadata file to other file formats."""
import abc
from typing import Optional, List, Any, Type

from common.models import SensorItem
from io_storage.storage import Storage


class BaseParser(metaclass=abc.ABCMeta):
    """this class is a base class for every parser"""
    def __init__(self, path: str, storage: Storage):
        self.file_path: str = path
        self._sensors: Optional[List[SensorItem]] = None
        self._body_pointer: Optional[int] = None
        self._data_pointer: Optional[int] = None
        self._storage = storage

    @abc.abstractmethod
    def next_item_with_class(self, item_class: Type[SensorItem]) -> Optional[SensorItem]:
        """this method will return a the next SensorItem found in the current file,
        of instance item_class"""
        pass

    def items_with_class(self, item_class: Type[SensorItem]) -> List[SensorItem]:
        """this method will return all SensorItems found in the current file,
         of instance item_class"""
        return []

    def next_item(self) -> Optional[SensorItem]:
        """this method will return a the next SensorItem found in the current file"""
        pass

    def items(self) -> List[SensorItem]:
        """this method will return all SensorItems found in the current file"""
        pass

    def format_version(self) -> Optional[str]:
        """this method will return the format version"""
        pass

    def serialize(self):
        """this method will write all the added items to file"""
        pass

    def compatible_sensors(self) -> List[Any]:
        """this method will return all SensorItem classes that are compatible
        with the current parser"""
        pass

    def add_items(self, items: List[SensorItem]):
        """this method will add items to be serialized"""
        self._sensors = items
        self._sensors.sort(key=lambda sensor_item: sensor_item.timestamp)

    def start_new_reading(self):
        """This method sets the reading file pointer to the body section of the metadata"""
        self._data_pointer = self._body_pointer
