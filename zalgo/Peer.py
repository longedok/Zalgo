from Packet import Packet

class Peer(object):
    __socket = None
    __out = []
    __to_receive = 0
    __packet = Packet()
    __buffer = ''

    def __init__(self, socket):
        self.__socket = socket
        self.__id = id

    def add_packet(self, packet):
        self.__out.append(packet)

    def ready_for_write(self):
        return len(self.__out)

    def get_next_chunk(self):
        if self.ready_for_write():
            if self.__buffer == '':
                return self.__out.pop().get_binary()
            else:
                tmp = self.__buffer
                self.__buffer = ''
                return tmp

    def set_buffer(self, data):
        self.__buffer = data
