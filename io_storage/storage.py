"""
This module enables the use of custom storage implementations e.g. cloud storage solutions without
changing the functionality of the scripts.
If one needs support for other type of storages they can just implement the Storage interface and
use the new storage type.
"""
import abc
import hashlib
import os
import logging

from typing import List

logger = logging.getLogger(__name__)


class Storage(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def container_name(self):
        pass

    @property
    @abc.abstractmethod
    def storage_url(self):
        pass

    @abc.abstractmethod
    def listdir(self, path: str) -> List[str]:
        pass

    @abc.abstractmethod
    def walk(self, path: str):
        pass

    @abc.abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abc.abstractmethod
    def isdir(self, path: str) -> bool:
        pass

    @abc.abstractmethod
    def isfile(self, path: str) -> bool:
        pass

    @abc.abstractmethod
    def open(self, path: str, mode='r'):
        pass

    def unique_file_identifier(self, file_path: str, block_size: int = 165536) -> str:
        md5_hash = hashlib.md5()
        with self.open(file_path, "rb") as file:
            for block in iter(lambda: file.read(block_size), b""):
                md5_hash.update(block)
        return str(md5_hash.hexdigest())

    def unique_path_identifier(self, path):
        return hashlib.md5(self.abs_path(path).encode()).hexdigest()

    @abc.abstractmethod
    def abs_path(self, path: str) -> str:
        pass

    @abc.abstractmethod
    def getsize(self, path: str) -> int:
        pass

    @abc.abstractmethod
    def getctime(self, path: str) -> float:
        pass

    @abc.abstractmethod
    def getmtime(self, path: str) -> float:
        pass

    @abc.abstractmethod
    def rename(self, src: str, dst: str):
        pass

    @abc.abstractmethod
    def remove(self, path: str):
        pass

    def put(self, data, destination):
        raise NotImplementedError()


class Local(Storage):

    @property
    def container_name(self):
        return ""

    @property
    def storage_url(self):
        return ""

    def listdir(self, path: str) -> List[str]:
        return os.listdir(path)

    def walk(self, path: str):
        yield os.walk(path)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def isdir(self, path: str) -> bool:
        return os.path.isdir(path)

    def isfile(self, path: str) -> bool:
        return os.path.isfile(path)

    def open(self, path: str, mode='r'):
        return open(path, mode)

    def abs_path(self, path: str) -> str:
        return os.path.abspath(path)

    def getsize(self, path: str) -> int:
        return os.path.getsize(path)

    def getctime(self, path: str) -> float:
        return os.path.getctime(path)

    def getmtime(self, path: str) -> float:
        return os.path.getmtime(path)

    def rename(self, src: str, dst: str):
        return os.rename(src, dst)

    def remove(self, path: str):
        return os.remove(path)

    def put(self, data, destination):
        with open(destination, "wb") as out_file:
            out_file.write(data)
