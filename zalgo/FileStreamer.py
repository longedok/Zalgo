from FileLoader import FileLoader
from DataProcessor import DataProcessor
from Debug import debug

class FileStreamer(object):
    def __init__(self, path, part_size):
        self.__part_size = part_size
        dp = DataProcessor()
        fl = FileLoader()
        self.__chunks = dp.split_data(fl.load_file(path), part_size)

    def get_chunk(self, start):
        return self.__chunks[start]
