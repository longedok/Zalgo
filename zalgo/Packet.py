import struct
import json

from Debug import debug

class Packet(object):
    def __init__(self, type=-1, ex_headers=[], content=''):
        self.type = type
        self.extra_headers = ex_headers
        self.content = content
        self.content_len = len(content)
        self.extra_headers_len = 0

    def set_extra_headers(self, headers_list):
        self.extra_headers = headers_list

    def get_binary(self):
        content = self.content
        ex_heads = json.dumps(self.extra_headers)
        header = struct.pack('!Bii', self.type, len(content), len(ex_heads))
        return header + ex_heads + content

    def __str__(self):
        return "Content len: %d; Extra headers: %s; Content[:10]: %s" % (self.content_len, 
                self.extra_headers, self.content[:10])
