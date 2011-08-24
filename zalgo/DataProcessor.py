import math

class DataProcessor(object):
    def __init__(self):
        pass

    def split_data(self, raw_data, piece_size = 100000):
        piece_count = int(math.ceil(len(raw_data) / float(piece_size)))
        pieces = []
        for i in xrange(piece_count):
            pieces.append(raw_data[i*piece_size:i*piece_size + piece_size])
        return pieces
