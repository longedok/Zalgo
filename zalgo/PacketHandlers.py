from PyQt4.QtCore import QObject, pyqtSignal, QFile, QByteArray

import Constants
from Database import Database
from Packet import Packet
from FileStreamer import FileStreamer
from ReceiveController import ReceiveController
from Debug import debug

class Handler(QObject):
    def __init__(self, network):
        super(Handler, self).__init__()
        self.network = network
        self.db = Database()

    def process_packet(self, sender, packet):
        pass

class HandshakeHandler(Handler):
    '''Process HANDSHAKE and HANDSHAKE_ACCEPT packets'''
    def __init__(self, network):
        super(HandshakeHandler, self).__init__(network)

    def process_packet(self, sender, packet):
        host, port = sender.getpeername()
        peer_id = packet.get_header_field('peer_id')
        debug('HandshakeHandler.process_packet(): peer_id is %s' % peer_id)
        if peer_id:
            self.network.register_pid(peer_id, host, port)        
            if packet.get_header_field('type') == Constants.HANDSHAKE:
                known_clients = self.network.get_clients_ips(peer_id)
                self.network.send(peer_id, Packet(Constants.HANDSHAKE_ACCEPT, 
                                                  {'peer_id': str(self.network.get_host_pid()),
                                                   'known_peers': known_clients}))
                debug('HandshakeHandler.packet_received(): Handshake complete.')
            elif packet.get_header_field('type') == Constants.HANDSHAKE_ACCEPT:
                to_connect = packet.get_header_field('known_peers')
                #if to_connect:
                    #for 
                debug('HandshakeHandler.packet_received(): Handshake Accept complete.')

class LookupHandler(Handler):
    def __init__(self, network):
        super(LookupHandler, self).__init__(network)
        self.__recent_lookups = []

    def process_packet(self, sender, packet):
        host, port = sender.getpeername()
        song_info = packet.get_header()
        packet_id = packet.get_header_field('packet_id')
        peer_id = self.network.get_pid_by_ip(host, port)
        if not packet_id:
            debug('LookupHandler.process_packet(): no packet_id')
            return
        if not packet_id in self.__recent_lookups:
            self.__recent_lookups.append(packet_id)
            clients = self.network.get_clients()
            for pid in filter(lambda x: x != peer_id, clients):
                self.network.send(pid, packet)
        if song_info:
            artist = song_info.get('artist') or ''
            title = song_info.get('title') or ''
            album = song_info.get('album') or ''
            
            search_results = self.db.lookup('title', 'artist', 'album', 'hash', 
                                            title=('LIKE', title), artist=('LIKE', artist), album=('LIKE', album))
        
            song_list = list()
            for entry in search_results:
                title, artist, album, _hash = entry
                song_list.append(dict(zip(['title', 'artist', 'album', 'hash'], 
                    [title, artist, album, _hash])))
            self.network.send(peer_id, Packet(Constants.FOUND, {'results': song_list}))     

class FoundHandler(Handler):
    musicFound = pyqtSignal(str, list)

    def __init__(self, network):
        super(FoundHandler, self).__init__(network)

    def process_packet(self, sender, packet):
        debug('Peer.packet_received() (FOUND): The incoming packet is %s' % packet.get_binary())
        host, port = sender.getpeername()
        pid = self.network.get_pid_by_ip(host, port)
        self.musicFound.emit(pid, packet.get_header_field('results'))

class StreamHandler(Handler):
    '''Process REQUEST_STREAM, REQUEST_PART, READY_TO_STREAM and CONTENT packets.'''
    streamCreated = pyqtSignal('QString', 'QString', int)
    packetReceived = pyqtSignal(int, 'QString', 'QByteArray')
    newPeerConnected = pyqtSignal('QString')

    def __init__(self, network):
        super(StreamHandler, self).__init__(network)
        self.__pid2stream = dict()          # peer_id to FileStreamer

    def process_packet(self, sender, packet):
        _type = packet.get_header_field('type')
        host, port = sender.getpeername()
        peer_id = self.network.get_pid_by_ip(host, port)
        
        if _type == Constants.REQUEST_STREAM:
            debug('StreamHandler.packet_received() (REQUEST_STREAM): %s' % packet.get_binary())
            file_hash = packet.get_header_field('hash')
            chunk_size = packet.get_header_field('chunk_size')
            stream_id = packet.get_header_field('packet_id')
            
            if (file_hash is not None) and chunk_size > 0:
                path = self.db.lookup('path', hash=('=', file_hash))
                if path:
                    self.__pid2stream[peer_id] = FileStreamer(path[0][0], chunk_size, stream_id)
                    size = self.__pid2stream[peer_id].get_size()
                    self.network.send(peer_id, Packet(Constants.READY_TO_STREAM, {'stream_id': stream_id, 'size': size}))
            else:
                debug("Peer.packet_received() (REQUEST_STREAM): No 'hash' or 'chunk_size' field was found in packet or 'chunk_size' is less or equal to 0")
                
        elif _type == Constants.REQUEST_PART:
            debug('StreaHandler.packet_received() (REQUEST_PART): %s' % packet.get_header())
            _from = packet.get_header_field('from')
            stream_id = packet.get_header_field('stream_id')
            if (_from is not None):
                chunk = self.__pid2stream[peer_id].get_chunk(_from)
                if chunk:
                    self.network.send(peer_id, Packet(Constants.CONTENT, 
                        {'from': _from, 'stream_id': stream_id}, chunk))
                    
        elif _type == Constants.READY_TO_STREAM:
            stream_id = packet.get_header_field('stream_id')
            file_size = packet.get_header_field('size')
            self.streamCreated.emit(stream_id, peer_id, file_size)             
                
        elif _type == Constants.CONTENT:
            stream_id = packet.get_header_field('stream_id')
            c_len = packet.get_header_field('content_len')
            _from = packet.get_header_field('from')
            self.packetReceived.emit(_from, peer_id, QByteArray(packet.get_content()))
                
    def send_packet_requests(self, stream_id, pids, packet_nums):
        for pid, packet_num in zip(pids, packet_nums):
            self.network.send(str(pid), Packet(Constants.REQUEST_PART, 
                                               {'stream_id': str(stream_id), 'from': packet_num}))
