from FileLoader import FileLoader
from DataProcessor import DataProcessor
from Debug import debug

class FileStreamer(object):
    def __init__(self, path, part_size, stream_id):
        self.__part_size = part_size
        dp = DataProcessor()
        fl = FileLoader()
        self.__chunks = dp.split_data(fl.load_file(path), part_size)
        debug('FileStreamer.init(): len(self.__chunks) == %d' % len(self.__chunks))
        self.__stream_id = stream_id

    def get_chunk(self, _from):
        if _from < len(self.__chunks):
            return self.__chunks[_from]
        else:
            return None
