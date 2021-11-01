import abc


class ExifGenerator(metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def create_exif(path: str) -> bool:
        pass

    @staticmethod
    @abc.abstractmethod
    def has_necessary_data(path: str) -> bool:
        pass
