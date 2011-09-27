import socket
import time
import select
import uuid
import json

from PyQt4.QtCore import QThread
from PyQt4.QtGui import qApp

import Constants
from Debug import debug
from SocketInfo import SocketInfo
from Packet import Packet

class Network(QThread):
    __port = 0
    __host = str()
    __sock = None
    __header_len = 9
    __host_pid = 0
    __sock2sockinfo = dict()
    __ip2pid = dict()
    __pid2sockinfo = dict()
    __event2handler = dict()
    __packetid2callback = dict()

    def __init__(self, host='localhost', port=13334):
        super(Network, self).__init__()
        self.__host = host
        self.__port = port
        self.__host_pid = uuid.uuid1()
        self.__buffer_size = 65536

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

    def subscribe(self, event, handler):
        ev2hand = self.__event2handler
        if not event in ev2hand.keys():
            ev2hand[event] = [handler]
        else:
            ev2hand[event].append(handler)

    def __create_client_socket(self, socket):
        debug('Network.__create_client_socket(): Creating client socket.')
        self.__sock2sockinfo[socket] = SocketInfo()

    def run(self):
        '''Accept incoming connections and send/receive packets to existing one.'''
        debug('Network.run(): Processing started.')    
        while 1:
            qApp.processEvents()
            # put all active sockets into 'sockets' variable
            sockets = self.__sock2sockinfo.keys()
            # select.select() checks if there are some sockets that are ready to be read or write
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
                            # all the parsing are consist of 3 steps:
                            # 1) We search for header in incoming binary (from 
                            # beggining to first null byte)
                            if sock_info.get_state() == Constants.RECEIVING_HEADER:
                                debug('Network.run(): Receiving header.')
                                buff = sock_info.get_buffer()
                                null_pos = buff.find('\0')
                                if null_pos > -1:
                                    header = buff[:null_pos]
                                    sock_info.set_buffer(buff[null_pos+1:])
                                    try:
                                        parsed_header = json.loads(header)
                                    except TypeError: # header is not in json format or json is invalid
                                        debug('Network.run(): Invalid header.')
                                    else: # all right, we can move to the next step
                                        sock_info.get_packet().set_header(parsed_header)
                                        content_len = sock_info.get_packet().get_header_field('content_len')
                                        if content_len and content_len > 0:
                                            sock_info.set_to_receive(content_len)
                                            sock_info.set_state(Constants.RECEIVING_CONTENT)
                                        else:
                                            sock_info.set_state(Constants.PACKET_RECEIVED)
                            # 2) Next, we receive the body of the packet, if it exists 
                            # (from first null byte read amount of bytes that is specifyed 
                            # in header)
                            if sock_info.get_state() == Constants.RECEIVING_CONTENT:
                                debug('Network.run(): Receiving content.')
                                buff = sock_info.get_buffer()
                                to_receive = sock_info.get_to_receive()
                                if len(buff) >= to_receive:
                                    sock_info.get_packet().set_content(buff[:to_receive])
                                    sock_info.set_buffer(buff[to_receive:])
                                    sock_info.set_state(Constants.PACKET_RECEIVED)
                            # 3) Finally, we pass received packet into processing function
                            # and reset SocketInfo structure to be ready to recieve new packets
                            if sock_info.get_state() == Constants.PACKET_RECEIVED:
                                debug('Network.run(): Packet received.')
                                packet = sock_info.get_packet()
                                _type = packet.get_header_field('type')
                                if (_type is not None):
                                    for handler in self.__event2handler[_type]:
                                        handler.process_packet(sock, packet)
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

    def register_pid(self, pid, host, port):
        self.__ip2pid[(host, port)] = pid
        clients = filter(lambda x: id(x) != id(self.__sock), self.__sock2sockinfo.keys())
        sock = filter(lambda x: (host, port) == x.getpeername(), clients)[0]
        self.__pid2sockinfo[pid] = self.__sock2sockinfo[sock]

    def get_host_pid(self):
        return self.__host_pid

    def get_clients(self):
        return self.__pid2sockinfo.keys()
    
    def get_clients_ips(self, exclude_pid=None):
        clients = self.get_clients()
        if exclude_pid:
            clients.remove(exclude_pid)
        return [self.__pid2sockinfo[pid].getpeername() for pid in clients]

if __name__ == '__main__':
    test = Network('localhost', 13333)
