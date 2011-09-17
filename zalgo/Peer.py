from PyQt4.QtCore import QObject

import Constants
from Packet import Packet, LookupPacket

class Peer(QObject):
    def __init__(self, network):
        super(Peer, self).__init__()
        self.network = network

    def lookup(self, search_string):
        connected_peers = self.network.get_clients()
        for pid in connected_peers:
            self.network.send(pid, LookupPacket({'title': str(search_string)}))

    def start_stream(self, pid, _hash):
        self.network.send(pid, Packet(Constants.REQUEST_STREAM, {'hash': _hash, 'chunk_size': 100000}))
