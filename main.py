import argparse

from zalgo.Network import Network

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed audio player.')
    parser.add_argument('--client', nargs='?', const='client', default='server', 
            help='Indicates that script should be launched in client mode (server mode is default).')
    args = parser.parse_args()
    server_mode = True if args.client == 'server' else False
    if server_mode:
        server = Network('localhost', 13333)
        server.create_socket()
    else:
        client = Network('localhost', 13334)
        client.create_socket()
        client.handshake_with('localhost', 13333)
