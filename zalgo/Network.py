import socket
import time
import select
import struct
import threading
import uuid
import json

import Constants
from Debug import debug
from SocketInfo import SocketInfo
from Packet import Packet

class Network(threading.Thread):
    __port = 0
    __host = ''
    __sock = None
    __header_len = 9
    __sock2sockinfo = {}
    __pid2sockinfo = {}
    __ip2pid = {}
    __host_pid = 0

    def __init__(self, host='localhost', port=13334):
        threading.Thread.__init__(self, name="Network")
        self.__host = host
        self.__port = port
        self.__host_pid = uuid.uuid1()

    def create_socket(self, peer_list = []):
        if self.__sock is None:
            self.__sock = socket.socket()
            self.__sock.setblocking(0)
            self.__sock.bind((self.__host, self.__port))
            self.__sock.listen(5)
            self.__sock2sockinfo[self.__sock] = None
            self.start()

    def connect(self, host, port):
        client_sockets = filter(lambda s: id(s) != id(self.__sock), 
                self.__sock2sockinfo.keys())
        sock = filter(lambda s: (host, port) == s.getpeername(), client_sockets)
        if not sock:
            sock = socket.socket()
            sock.setblocking(0)
            try:
                sock.connect((host, port))
            finally:
                debug('Network.connect(): Creating client socket.')
                self.__create_client_socket(sock, self.__header_len)
                return sock
        else:
            return sock

    def handshake_with(self, host, port):
        if not (host, port) in self.__ip2pid.keys():
            sock = self.connect(host, port)
            packet = Packet(Constants.HANDSHAKE, [{'peer_id': str(self.__host_pid)}])
            self.__sock2sockinfo[sock].append_send_queue(packet)
            debug('Network.handshake_with(): doing handshake with: %s:%d' % (host, port))

    def send(self, peer_id, packet):
        self.__pid2sockinfo[peer_id].append_send_queue(packet)

    def __create_client_socket(self, socket, to_receive):
        debug('Network.__create_client_socket(): Creating client socket.')
        self.__sock2sockinfo[socket] = SocketInfo(self.__header_len, Constants.RECEIVING_HEADERS)

    def run(self):
        '''Process incoming connections and sending/receiveing packets.'''
        debug('Network.run(): Processing started.')
        while 1:
            for_read, for_write, ex = select.select(self.__sock2sockinfo.keys(), 
                    self.__sock2sockinfo.keys(), self.__sock2sockinfo.keys(), 0)
            if len(for_read) > 0:
                for sock in for_read:
                    if sock == self.__sock: # host socket ready to be read
                        client_sock, addr = self.__sock.accept()
                        debug("Network.run(): Client %s:%d connected." % addr)
                        self.__create_client_socket(client_sock, self.__header_len)
                    else: # one of the client sockets ready to be read
                        try:
                            received = sock.recv(self.__sock2sockinfo[sock].get_to_receive())
                        except:
                            debug("Network.run(): Client %s:%d disconnected." % sock.getpeername())
                            del self.__sock2sockinfo[sock]
                            for_write.remove(sock)
                            continue
                        debug(self.__sock2sockinfo[sock].get_buffer())
                        self.__sock2sockinfo[sock].append_buffer(received)
                        debug(self.__sock2sockinfo[sock].get_buffer())
                        to_receive = self.__sock2sockinfo[sock].get_to_receive()
                        self.__sock2sockinfo[sock].set_to_receive(to_receive - len(received))
                        if len(received) == 0:
                            debug("Network.run(): Client %s:%d disconnected." % sock.getpeername())
                            del self.__sock2sockinfo[sock]
                            for_write.remove(sock)
                            sock.close()
                        else:
                            # State machine for packet parsing
                            state = self.__sock2sockinfo[sock].get_state()
                            if state == Constants.RECEIVING_HEADERS:
                                debug('Network.run(): Receiving header.')
                                if self.__sock2sockinfo[sock].get_to_receive() == 0:
                                    packet_type, content_len, extra_header_len = struct.unpack("!Bii", 
                                            self.__sock2sockinfo[sock].get_buffer())
                                    self.__sock2sockinfo[sock].get_packet().type = packet_type
                                    self.__sock2sockinfo[sock].get_packet().content_len = content_len
                                    if extra_header_len > 0:
                                        self.__sock2sockinfo[sock].set_state(Constants.RECEIVING_EX_HEADERS)
                                        self.__sock2sockinfo[sock].set_to_receive(extra_header_len)
                                    elif content_len > 0:
                                        self.__sock2sockinfo[sock].set_state(Constants.RECEIVING_CONTENT)
                                        self.__sock2sockinfo[sock].set_to_receive(content_len)
                                    else:
                                        self.__sock2sockinfo[sock].set_state(Constants.PACKET_RECEIVED)
                                    debug('Network.run(): Header received.')
                                    self.__sock2sockinfo[sock].set_buffer('')
                            elif state == Constants.RECEIVING_EX_HEADERS:
                                debug('Network.run(): Receiving extra headers.')
                                if self.__sock2sockinfo[sock].get_to_receive() == 0:
                                    try:
                                        json_data = json.loads(self.__sock2sockinfo[sock].get_buffer())
                                    except TypeError:
                                        debug('Network.run(): Invalid extra headers.')
                                    else:
                                        self.__sock2sockinfo[sock].get_packet().extra_headers = json_data
                                    if self.__sock2sockinfo[sock].get_packet().content_len > 0:
                                        self.__sock2sockinfo[sock].set_state(Constants.RECEIVING_CONTENT)
                                    else:
                                        self.__sock2sockinfo[sock].set_state(Constants.PACKET_RECEIVED)
                                    self.__sock2sockinfo[sock].set_to_receive(
                                            self.__sock2sockinfo[sock].get_packet().content_len)
                                    debug('Network.run(): Extra headers received.')
                                    self.__sock2sockinfo[sock].set_buffer('')
                            elif state == Constants.RECEIVING_CONTENT:
                                debug('Network.run(): Receiving content.')
                                if self.__sock2sockinfo[sock].get_to_receive() == 0:
                                    self.__sock2sockinfo[sock].get_packet().content = self.__sock2sockinfo[sock].get_buffer()
                                    self.__sock2sockinfo[sock].set_state(Constants.PACKET_RECEIVED)
                                    debug('Network.run(): Content received.')
                            state = self.__sock2sockinfo[sock].get_state()
                            if state == Constants.PACKET_RECEIVED:
                                self.__sock2sockinfo[sock].set_buffer('')
                                self.__sock2sockinfo[sock].set_to_receive(self.__header_len)
                                self.packet_received(sock, self.__sock2sockinfo[sock].get_packet())
                                self.__sock2sockinfo[sock].set_packet(Packet())
                                self.__sock2sockinfo[sock].set_state(Constants.RECEIVING_HEADERS)
                                debug('Network.run(): Packet received.')

            if len(for_write) > 0:
                for sock in for_write:
                    if self.__sock2sockinfo[sock].ready_for_write():
                        content = self.__sock2sockinfo[sock].get_next_chunk()
                        sended = sock.send(content)
                        if sended < len(content):
                            self.__sock2sockinfo[sock].set_out_buffer(content[sended:])
            time.sleep(0.01)

    def __resolve_peer_id(self, host, port):
        return self.__ip2pid[(host, port)]

    def __register_pid(self, pid, host, port):
        self.__ip2pid[(host, port)] = pid
        clients = filter(lambda x: id(x) != id(self.__sock), self.__sock2sockinfo.keys())
        sock = filter(lambda x: (host, port) == x.getpeername(), clients)[0]
        self.__pid2sockinfo[pid] = self.__sock2sockinfo[sock]

    def packet_received(self, sender, packet):
        host, port = sender.getpeername()
        if packet.type == Constants.HANDSHAKE:
            pid = packet.extra_headers[0].get('peer_id')
            if pid:
                self.__register_pid(pid, host, port)
                self.send(pid, Packet(Constants.HANDSHAKE_ACCEPT, [{'peer_id': str(self.__host_pid)}]))
                debug('Network.packet_received(): Handshake complete.')
        if packet.type == Constants.HANDSHAKE_ACCEPT:
            pid = packet.extra_headers[0].get('peer_id')
            if pid:
                self.__register_pid(pid, host, port)
                debug('Network.packet_received(): Handshake accept complete.')
        if packet.type == Constants.LOOKUP:
            song_info = packet.extra_headers[0]
            artist = song_info.get('artist') or ''
            title = song_info.get('title') or ''
            album = song_info.get('album') or ''
            search_results = self.__file_loader.lookup('title', 'artist', 'album', 'hash', 
                    title=('LIKE', title), artist=('LIKE', artist), album=('LIKE', album))
            extra_headers = []
            for entry in search_results:
                title, artist, album, hash = entry
                extra_headers.append(dict(zip(['title', 'artist', 'album', 'hash'], [title, artist, album, hash])))
            answer_packet = Packet(FOUND, extra_headers)
            debug('Peer.packet_received() (LOOKUP): The outcoming packet is %s' % answer_packet.pack())
        elif packet.type == Constants.FOUND:
            debug('Peer.packet_received() (FOUND): The incoming packet is %s' % packet.pack())
        elif packet.type == Constants.REQUEST_SREAM:
            pass
        elif packet.type == Constants.READY_TO_STREAM:
            pass
        elif packet.type == Constants.REQUEST_PART:
            pass
        elif packet.type == Constants.CONTENT:
            self.__sp.add_chunk(packet.content)
            if self.first_time:
                self.__sp.play()
                self.first_time = False

if __name__ == '__main__':
    test = Network('localhost', 13333)
