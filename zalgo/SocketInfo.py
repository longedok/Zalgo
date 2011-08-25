import Constants
from Packet import Packet
from Debug import debug

class SocketInfo(object):
    __out = []
    __to_receive = 0
    __packet = Packet()
    __in_buffer = ''
    __out_buffer = ''
    __state = Constants.RECEIVING_HEADER

    def __init__(self):
        pass

    def ready_for_write(self):
        return len(self.__out)

    def get_next_chunk(self):
        if self.ready_for_write():
            if self.__out_buffer == '':
                return self.__out.pop().get_binary()
            else:
                return self.__out_buffer
        else:
            return None

    def set_out_buffer(self, data):
        self.__out_buffer = data

    def set_buffer(self, data):
        self.__in_buffer = data

    def get_buffer(self):
        return self.__in_buffer

    def append_buffer(self, data):
        self.__in_buffer += data

    def get_to_receive(self):
        return self.__to_receive

    def set_to_receive(self, count):
        self.__to_receive = count

    def get_state(self):
        return self.__state

    def set_state(self, state):
        self.__state = state

    def get_packet(self):
        return self.__packet

    def set_packet(self, packet):
        self.__packet = packet

    def append_send_queue(self, packet):
        debug('SocketInfo.append_send_queue(): %s' % str(packet))
        self.__out.append(packet)
