import math
import socket
import time
import select
import struct
import random
import threading
import os

import pymedia.muxer as muxer
import pymedia.audio.acodec as acodec
import pymedia.audio.sound as sound

class FileLoader(object):
    def __init__(self, pathes = []):
        self.__pathes = pathes[:]

    def index_files(self):
        pass

    def load_file(self, name):
        try:
            fobject = open(name, 'rb')
            fraw_data = fobject.read()
        except IOError:
            return None
        return fraw_data

class StreamPlayer(threading.Thread):
    __decoder = None
    __sound_device = None
    __buffer = ''
    __is_playing = False
    
    def __init__(self):
        threading.Thread.__init__(self, name="StreamPlayer")
        self.__demuxer = muxer.Demuxer('mp3')
        self.start()

    def add_chunk(self, chunk):
        self.__buffer += chunk

    def play(self):
        self.__is_playing = True

    def pause(self):
        self.__sound_device.pause()

    def unpause(self):
        self.__sound_device.unpause()

    def run(self):
        rate = 1
        card = 0
        while True and self.__is_playing:
            frames = self.__demuxer.parse(self.__buffer)
            self.__buffer = ''
            for frame in frames:
                if self.__decoder == None:
                    self.__decoder = acodec.Decoder(self.__demuxer.streams[frame[0]])
                raw = self.__decoder.decode(frame[1])
                if raw and raw.data:
                    if self.__sound_device == None:
                        self.__sound_device = sound.Output(int(raw.sample_rate * rate), raw.channels, sound.AFMT_S16_LE, card)
                    self.__sound_device.play(raw.data)

class DataProcessor(object):
    def __init__(self):
        pass

    def split_data(self, raw_data, piece_size = 100000):
        piece_count = int(math.ceil(len(raw_data) / float(piece_size)))
        pieces = []
        for i in xrange(piece_count):
            pieces.append(raw_data[i*piece_size:i*piece_size + piece_size])
        return pieces

class Network(threading.Thread):
    __port = 0
    __host = ''
    __sock = None
    sockets = {}

    def __init__(self, host='localhost', port=13334):
        threading.Thread.__init__(self, name="Network")
        self.__port = port
        self.__host = host

    def enter_the_net(self, peer_list = []):
        if self.__sock is None:
            self.__sock = socket.socket()
            self.__sock.setblocking(0)
            self.__sock.bind((self.__host, self.__port))
            self.__sock.listen(5)
            self.sockets[self.__sock] = None
            self.start()

    def connect_to(self, host, port):
        sock = socket.socket()
        sock.connect((host, port))
        self.sockets[sock] = {'out': [], 'in': '', 'to_receive': 0}

    def data_received(self, sender, data):
        pass

    def send(self, data):
        test_sock = filter(lambda x: x != self.__sock, self.sockets.keys())[0]
        data_processor = DataProcessor()
        for piece in reversed(data_processor.split_data(data)):
            header = struct.pack('!Bi', 1, len(piece))
            self.sockets[test_sock]['out'].append(header + piece)

    def run(self):
        header_len = 5
        while 1:
            for_read, for_write, ex = select.select(self.sockets.keys(), 
                    self.sockets.keys(), self.sockets.keys(), 0)
            #print "for read: %s" % str(["%s:%d" % sock.getpeername() for sock in for_read if sock != self.__sock])
            if len(ex) > 0:
                print ex
            if len(for_read) > 0:
                for sock in for_read:
                    if sock == self.__sock:
                        client_sock, addr = self.__sock.accept()
                        print "client %s:%d connected" % addr
                        self.sockets[client_sock] = {'out': [], 'in': '', 'to_receive': 0}
                    else:
                        receiving_header = False
                        if self.sockets[sock]['to_receive'] == 0:
                            self.sockets[sock]['to_receive'] = header_len
                            receiving_header = True
                        received = sock.recv(self.sockets[sock]['to_receive'])
                        if len(received) == 0:
                            print "client %s:%d disconnected" % sock.getpeername()
                            del self.sockets[sock]
                            for_write.remove(sock)
                            sock.close()
                        else:
                            self.sockets[sock]['in'] += received
                            self.sockets[sock]['to_receive'] -= len(received)
                            if self.sockets[sock]['to_receive'] == 0:
                                addr, port = sock.getpeername()
                                if receiving_header:
                                    packet_type, packet_len = struct.unpack("!Bi", self.sockets[sock]['in'])
                                    print 'header of packet of type %d and with payload length %d was received from peer %s:%d' % (packet_type, packet_len, addr, port)
                                    self.sockets[sock]['to_receive'] = packet_len
                                    receiving_header = False
                                else:
                                    self.data_received(sock, self.sockets[sock]['in'])
                                self.sockets[sock]['in'] = ''
            if len(for_write) > 0:
                for sock in for_write:
                    if len(self.sockets[sock]['out']) > 0:
                        packet = self.sockets[sock]['out'].pop()
                        sock.sendall(packet)
            time.sleep(0.01)

class Peer(Network):
    __peer_list = []
    first_time = True

    def __init__(self, host, port):
        super(Peer, self).__init__(host, port)
        self.__sp = StreamPlayer()

    def data_received(self, sender, data):
        self.__sp.add_chunk(data)
        if self.first_time:
            self.__sp.play()
            self.first_time = False

if __name__ == '__main__':
    #sp = StreamPlayer()
    #fload = FileLoader()
    #datap = DataProcessor()
    #raw = fload.load_file('test3.mp3')
    #chunks = datap.split_data(raw)
    #for chunk in chunks:
        #sp.add_chunk(chunk)
    #sp.play()

    import sys
    port = int(sys.argv[1])
    if port == 1:
        port = 13333
    if port == 2:
        port = 13334
    peer = Peer('localhost', port)
    peer.enter_the_net()
    if sys.argv[2] == '1':
        ip = sys.argv[3]
        peer.enter_the_net()
        peer.connect_to(ip, 13333)
        fload = FileLoader()
        raw = fload.load_file('test3.mp3')
        if raw:
            print "file loaded"
            peer.send(raw)
