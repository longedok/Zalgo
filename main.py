import argparse
import time

import zalgo.Constants as Constants
from zalgo.Network import Network
from zalgo.Packet import Packet
from zalgo.Debug import debug
from zalgo.FileLoader import FileLoader

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed audio player.')
    parser.add_argument('--client', nargs='?', const='client', default='server', 
            help='Indicates that script should be launched in client mode (server mode is default).')
    args = parser.parse_args()
    server_mode = True if args.client == 'server' else False
    if server_mode:
        #fl = FileLoader(['D:/music'])
        #fl.index_files()
        server = Network('localhost', 13333)
        server.create_socket()
    else:
        client = Network('localhost', 13334)
        client.create_socket()
        client.handshake_with('localhost', 13333)
        time.sleep(1)
        server_pid = client.get_pid_by_ip('127.0.0.1', 13333)
        if server_pid:
            client.send(server_pid, Packet(Constants.LOOKUP, {'title': 'Starlight'}))
