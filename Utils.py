from Peer import Peer


def read_peers_from_file(peers_file_path):
    peers = []

    with open(peers_file_path, 'rb') as peers_file:
        connections = peers_file.readlines()
        for connection in connections:
            ip, port = connection.decode().strip('\r\n').split(',')
            port = int(port)
            peer = Peer(ip=ip, port=port)

            peers.append(peer)

    return peers
