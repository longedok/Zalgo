import json
import time
import random

from Debug import debug

class Packet(object):

    def __init__(self, _type=-1, header=dict(), content=str()):
        self.__header = dict()
        self.__content = str()
        self.set_header(header)
        self.set_content(content)
        self.set_header_field('packet_id', self.__generate_id())
        self.set_header_field('type', _type)
        self.set_header_field('content_len', len(self.get_content()))

    def __generate_id(self):
        unix_time = str(int(time.time() * 1000))
        random_postfix = ''.join([chr(random.randint(ord('a'), ord('z'))) for _ in xrange(4)])
        return unix_time + random_postfix

    def set_content(self, content):
        self.__content = content

    def get_content(self):
        return self.__content

    def set_header(self, header):
        self.__header = header

    def get_header(self):
        return self.__header

    def set_header_field(self, field_name, value):
        self.__header[field_name] = value

    def get_header_field(self, field_name):
        return self.__header.get(field_name.lower())

    def get_binary(self):
        return json.dumps(self.__header) + '\0' + self.__content

    def __str__(self):
        return "Header: %s" % (self.__header)

if __name__ == '__main__':
    p = Packet(1, {'title': 'starlight'})
    print p.get_header()
