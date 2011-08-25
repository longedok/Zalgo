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
from Database import Database

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
        self.__db = Database()
        self.__buffer_size = 8192

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
                self.__create_client_socket(sock)
                return sock
        else:
            return sock

    def handshake_with(self, host, port):
        if not (host, port) in self.__ip2pid.keys():
            sock = self.connect(host, port)
            packet = Packet(Constants.HANDSHAKE, {'peer_id': str(self.__host_pid)})
            self.__sock2sockinfo[sock].append_send_queue(packet)
            debug('Network.handshake_with(): doing handshake with: %s:%d' % (host, port))

    def send(self, peer_id, packet):
        debug('Network.send(): Send packet to %s' % str(peer_id))
        self.__pid2sockinfo[peer_id].append_send_queue(packet)

    def __create_client_socket(self, socket):
        debug('Network.__create_client_socket(): Creating client socket.')
        self.__sock2sockinfo[socket] = SocketInfo()

    def run(self):
        '''Accept incoming connections and send/receive packets to existing one.'''
        debug('Network.run(): Processing started.')
        while 1:
            # put all active sockets into 'sockets' variable
            sockets = self.__sock2sockinfo.keys()
            # select.select() checks if there are some sockets that ready to be read or write
            for_read, for_write, _ = select.select(sockets, sockets, sockets, 0)
            if len(for_read) > 0:
                # process sockets that is ready to be read
                for sock in for_read:
                    if sock == self.__sock: # current socket is a host socket
                        # accept new connection
                        client_sock, addr = self.__sock.accept()
                        debug("Network.run(): Client %s:%d connected." % addr)
                        self.__create_client_socket(client_sock)
                    else: # current socket is a client socket
                        # receive data from that client socket
                        try:
                            # receive maximum 8192 bytes from net buffer
                            received = sock.recv(self.__buffer_size)
                        except:
                            # getting error during receiving means
                            # that something goes wrong with socket and it was closed. 
                            # so we delete it from our __sock2sockinfo dict
                            debug("Network.run(): Client %s:%d disconnected." % sock.getpeername())
                            del self.__sock2sockinfo[sock]
                            for_write.remove(sock)
                            continue
                        # append received data to socket buffer
                        self.__sock2sockinfo[sock].append_buffer(received)
                        if len(received) == 0:
                            # receiving 0 bytes means, that socket was closed by the other side.
                            # so we close it too.
                            debug("Network.run(): Client %s:%d disconnected." % sock.getpeername())
                            del self.__sock2sockinfo[sock]
                            for_write.remove(sock)
                            sock.close()
                        else:
                            # we recived more than 0 bytes! Now we should parse received data
                            # and put it into Packet() structure or store it into socket buffer
                            # (if we doesn't receive the whole packet).
                            sock_info = self.__sock2sockinfo[sock]
                            if sock_info.get_state() == Constants.RECEIVING_HEADER:
                                debug('Network.run(): Receiving header.')
                                buff = sock_info.get_buffer()
                                null_pos = buff.find('\0')
                                if null_pos > -1:
                                    header = buff[:null_pos]
                                    sock_info.set_buffer(buff[null_pos+1:])
                                    try:
                                        parsed_header = json.loads(header)
                                    except TypeError:
                                        debug('Network.run(): Invalid header.')
                                    else:
                                        sock_info.get_packet().set_header(parsed_header)
                                        content_len = sock_info.get_packet().get_header_field('content_len')
                                        if content_len and content_len > 0:
                                            sock_info.set_to_receive(content_len)
                                            sock_info.set_state(Constants.RECEIVING_CONTENT)
                                        else:
                                            sock_info.set_state(Constants.PACKET_RECEIVED)
                            if sock_info.get_state() == Constants.RECEIVING_CONTENT:
                                debug('Network.run(): Receiving content.')
                                buff = sock_info.get_buffer()
                                to_receive = sock_info.get_to_receive()
                                if len(buff) >= to_receive:
                                    sock_info.get_packet().set_content(buff[:to_receive])
                                    sock_info.set_buffer(buff[to_receive:])
                                    sock_info.set_state(Constants.PACKET_RECEIVED)
                            if sock_info.get_state() == Constants.PACKET_RECEIVED:
                                self.packet_received(sock, sock_info.get_packet())
                                sock_info.set_state(Constants.RECEIVING_HEADER)
                                sock_info.set_packet(Packet())
            if len(for_write) > 0:
                for sock in for_write:
                    sock_info = self.__sock2sockinfo[sock]
                    if sock_info.ready_for_write():
                        content = sock_info.get_next_chunk()
                        sended = sock.send(content)
                        if sended < len(content):
                            sock_info.set_out_buffer(content[sended:])
            time.sleep(0.01)

    def get_pid_by_ip(self, host, port):
        debug('Network.get_pid_by_ip(): %s' % self.__ip2pid)
        return self.__ip2pid.get((host, port))

    def __register_pid(self, pid, host, port):
        self.__ip2pid[(host, port)] = pid
        clients = filter(lambda x: id(x) != id(self.__sock), self.__sock2sockinfo.keys())
        sock = filter(lambda x: (host, port) == x.getpeername(), clients)[0]
        self.__pid2sockinfo[pid] = self.__sock2sockinfo[sock]

    def packet_received(self, sender, packet):
        debug('Network.packet_received(): Packet received.')
        host, port = sender.getpeername()
        debug(packet)
        packet_type = packet.get_header_field('type')
        if packet_type is None:
            debug('Network.packet_received(): Received packet without type. Processing of that packet stopped.')
            return
        if packet_type == Constants.HANDSHAKE:
            pid = packet.get_header_field('peer_id')
            if pid:
                self.__register_pid(pid, host, port)
                self.send(pid, Packet(Constants.HANDSHAKE_ACCEPT, {'peer_id': str(self.__host_pid)}))
                debug('Network.packet_received(): Handshake complete.')
        if packet_type == Constants.HANDSHAKE_ACCEPT:
            pid = packet.get_header_field('peer_id')
            if pid:
                self.__register_pid(pid, host, port)
                debug('Network.packet_received(): Handshake accept complete (%s:%d).' % (host, port))
        if packet_type == Constants.LOOKUP:
            song_info = packet.get_header()
            if song_info:
                artist = song_info.get('artist') or ''
                title = song_info.get('title') or ''
                album = song_info.get('album') or ''
                search_results = self.__db.lookup('title', 'artist', 'album', 'hash', 
                        title=('LIKE', title), artist=('LIKE', artist), album=('LIKE', album))
                song_list = list()
                for entry in search_results:
                    title, artist, album, hash = entry
                    song_list.append(dict(zip(['title', 'artist', 'album', 'hash'], [title, artist, album, hash])))
                header = {'result': song_list, 'peer_id': str(self.__host_pid)}
                answer_packet = Packet(Constants.FOUND, header)
                debug('Peer.packet_received() (LOOKUP): The outcoming packet is %s' % answer_packet.get_binary())
        elif packet_type == Constants.FOUND:
            debug('Peer.packet_received() (FOUND): The incoming packet is %s' % packet.pack())
        elif packet_type == Constants.REQUEST_SREAM:
            pass
        elif packet_type == Constants.READY_TO_STREAM:
            pass
        elif packet_type == Constants.REQUEST_PART:
            pass
        elif packet_type == Constants.CONTENT:
            self.__sp.add_chunk(packet.content)
            if self.first_time:
                self.__sp.play()
                self.first_time = False

if __name__ == '__main__':
    test = Network('localhost', 13333)
