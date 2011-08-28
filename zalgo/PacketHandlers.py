import Constants
from Database import Database
from Packet import Packet
from FileStreamer import FileStreamer
from ReceiveController import ReceiveController
from Debug import debug

class Handler(object):
    def __init__(self, network):
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
                self.network.send(peer_id, Packet(Constants.HANDSHAKE_ACCEPT, {'peer_id': str(self.network.get_host_pid())}))
                debug('HandshakeHandler.packet_received(): Handshake complete.')
            debug('HandshakeHandler.packet_received(): Handshake Accept complete.')

class LookupHandler(Handler):
    def __init__(self, network):
        super(LookupHandler, self).__init__(network)

    def process_packet(self, sender, packet):
        host, port = sender.getpeername()
        song_info = packet.get_header()
        if song_info:
            peer_id = self.get_pid_by_ip(host, port)
            artist = song_info.get('artist') or ''
            title = song_info.get('title') or ''
            album = song_info.get('album') or ''
            def process_result(search_results):
                song_list = list()
                for entry in search_results:
                    title, artist, album, _hash = entry
                    song_list.append(dict(zip(['title', 'artist', 'album', 'hash'], 
                        [title, artist, album, _hash])))
                self.network.send(peer_id, Packet(Constants.FOUND, {'results': song_list}))
            self.db.lookup(process_result, 'title', 'artist', 'album', 'hash', 
                    title=('LIKE', title), artist=('LIKE', artist), album=('LIKE', album))

class FoundHandler(Handler):
    def __init__(self, network):
        super(FoundHandler, self).__init__(network)

    def process_packet(self, sender, packet):
        debug('Peer.packet_received() (FOUND): The incoming packet is %s' % packet.get_binary())

class StreamHandler(Handler):
    '''Process REQUEST_STREAM, REQUEST_PART, READY_TO_STREAM and CONTENT packets.'''
    def __init__(self, network):
        super(StreamHandler, self).__init__(network)
        self.__pid2stream = dict()          # peer_id to FileStreamer
        self.__sid2receives = dict()        # stream_id to ReceiveController

    def process_packet(self, sender, packet):
        _type = packet.get_header_field('type')
        host, port = sender.getpeername()
        peer_id = self.network.get_pid_by_ip(host, port)
        if _type == Constants.REQUEST_STREAM:
            debug('StreamHandler.packet_received() (REQUEST_STREAM): %s' % packet.get_binary())
            file_hash = packet.get_header_field('hash')
            chunk_size = packet.get_header_field('chunk_size')
            stream_id = packet.get_header_field('packet_id')
            def path_found(path):
                if path:
                    self.__pid2stream[peer_id] = FileStreamer(path[0][0], chunk_size, stream_id)
                    self.network.send(peer_id, Packet(Constants.READY_TO_STREAM, {'stream_id': stream_id}))
            if (file_hash is not None) and chunk_size > 0:
                self.db.lookup(path_found, 'path', hash=('=', file_hash))
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
            if not stream_id in self.__sid2receives.keys():
                self.__sid2receives[stream_id] = ReceiveController(peer_id)
                targets_list = self.__sid2receives[stream_id].get_packet_requests()
                for target_pid, _from in targets_list:
                    self.network.send(target_pid, Packet(Constants.REQUEST_PART, 
                        {'stream_id': stream_id, 'from': _from}))
            else:
                self.__sid2receives[stream_id].add_peer(peer_id)
        elif _type == Constants.CONTENT:
            stream_id = packet.get_header_field('stream_id')
            _from = packet.get_header_field('from')
            recv_contr = self.__sid2receives[stream_id]
            recv_contr.receive_packet(_from, peer_id, packet.get_content())
            for target_pid, _from in recv_contr.get_packet_requests():
                self.network.send(target_pid, Packet(Constants.REQUEST_PART, 
                    {'stream_id': stream_id, 'from': _from}))
