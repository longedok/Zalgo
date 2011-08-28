import argparse
import time

import zalgo.Constants as Constants
from zalgo.Network import Network
from zalgo.Packet import Packet
from zalgo.Debug import debug
from zalgo.FileLoader import FileLoader
from zalgo.PacketHandlers import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed audio player.')
    parser.add_argument('--client', nargs='?', const='client', default='server', 
            help='Indicates that script should be launched in client mode (server mode is default).')
    args = parser.parse_args()
    server_mode = True if args.client == 'server' else False
    if server_mode:
        server = Network('localhost', 13333)
        handshake_handler = HandshakeHandler(server)
        server.subscribe(Constants.HANDSHAKE, handshake_handler)
        server.subscribe(Constants.HANDSHAKE_ACCEPT, handshake_handler)
        server.subscribe(Constants.LOOKUP, LookupHandler(server))
        server.subscribe(Constants.FOUND, FoundHandler(server))
        stream_handler = StreamHandler(server)
        server.subscribe(Constants.REQUEST_STREAM, stream_handler)
        server.subscribe(Constants.REQUEST_PART, stream_handler)
        server.subscribe(Constants.READY_TO_STREAM, stream_handler)
        server.subscribe(Constants.CONTENT, stream_handler)
        server.create_socket()
    else:
        client = Network('localhost', 13334)
        handshake_handler = HandshakeHandler(client)
        client.subscribe(Constants.HANDSHAKE, handshake_handler)
        client.subscribe(Constants.HANDSHAKE_ACCEPT, handshake_handler)
        client.subscribe(Constants.LOOKUP, LookupHandler(client))
        client.subscribe(Constants.FOUND, FoundHandler(client))
        stream_handler = StreamHandler(client)
        client.subscribe(Constants.REQUEST_STREAM, stream_handler)
        client.subscribe(Constants.REQUEST_PART, stream_handler)
        client.subscribe(Constants.READY_TO_STREAM, stream_handler)
        client.subscribe(Constants.CONTENT, stream_handler)
        client.create_socket()
        client.handshake_with('localhost', 13333)
        time.sleep(1)
        server_pid = client.get_pid_by_ip('127.0.0.1', 13333)
        if server_pid:
            client.send(server_pid, Packet(Constants.REQUEST_STREAM, {'hash': '49bab585ee182a42e96da4b830290c5dc43e398e', 'chunk_size': 100000}))
            time.sleep(1)
