import argparse
import time
import sys

import sip
sip.setapi('QString', 2)

from PyQt4 import QtGui

import zalgo.Constants as Constants
from zalgo.Network import Network
from zalgo.Packet import Packet, LookupPacket
from zalgo.Debug import debug
from zalgo.FileLoader import FileLoader
from zalgo.PacketHandlers import *
from zalgo.MainWindow import MainWindow
from zalgo.Peer import Peer
from zalgo.ReceiveController import ReceiveController
from zalgo.StreamAdapter import StreamAdapter

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed audio player.')
    parser.add_argument('--client', nargs='?', const='client', default='server', 
            help='Indicates that script should be launched in client mode (server mode is default).')
    args = parser.parse_args()
    server_mode = True if args.client == 'server' else False
    
    app = QtGui.QApplication(sys.argv)
    
    if server_mode:
        server = Network('localhost', 13333)
        
        handshake_handler = HandshakeHandler(server)
        server.subscribe(Constants.HANDSHAKE, handshake_handler)
        server.subscribe(Constants.HANDSHAKE_ACCEPT, handshake_handler)
        
        stream_handler = StreamHandler(server)
        server.subscribe(Constants.REQUEST_STREAM, stream_handler)
        server.subscribe(Constants.REQUEST_PART, stream_handler)
        server.subscribe(Constants.READY_TO_STREAM, stream_handler)
        server.subscribe(Constants.CONTENT, stream_handler)
        
        server.subscribe(Constants.LOOKUP, LookupHandler(server))
        server.subscribe(Constants.FOUND, FoundHandler(server))
        
        server.create_socket()
    else:
        stream_adapter = StreamAdapter()
        recv_contr = ReceiveController()
        recv_contr.contentReceived.connect(stream_adapter.receive_data)
        
        client = Network('localhost', 13334)
          
        main_window = MainWindow(Peer(client), stream_adapter)
        recv_contr.streamCreated.connect(main_window.streamCreated)
        
        handshake_handler = HandshakeHandler(client)
        client.subscribe(Constants.HANDSHAKE, handshake_handler)
        client.subscribe(Constants.HANDSHAKE_ACCEPT, handshake_handler)
        
        stream_handler = StreamHandler(client)
        client.subscribe(Constants.REQUEST_STREAM, stream_handler)
        client.subscribe(Constants.REQUEST_PART, stream_handler)
        client.subscribe(Constants.READY_TO_STREAM, stream_handler)
        client.subscribe(Constants.CONTENT, stream_handler)
        recv_contr.nextPacketRequests.connect(stream_handler.send_packet_requests)
        stream_handler.streamCreated.connect(recv_contr.recreate)
        stream_handler.packetReceived.connect(recv_contr.receive_packet)
        stream_handler.newPeerConnected.connect(recv_contr.add_peer)
        
        found_handler = FoundHandler(client)
        client.subscribe(Constants.FOUND, found_handler)
        found_handler.musicFound.connect(main_window.musicFound)
         
        client.subscribe(Constants.LOOKUP, LookupHandler(client))
        
        client.create_socket()
        client.handshake_with('localhost', 13333)  
     
        main_window.show()
        
    sys.exit(app.exec_())
    client.stop()
