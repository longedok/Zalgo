class FileStreamer(object):
    def __init__(self, hash, part_size):
        self.__hash = hash
        self.__part_size = part_size
        self.__chunks = []
        self.__file_loader = FileLoader()

    def get_chunks(self, start, end):
        return self.__chunks[start, end]
