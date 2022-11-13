import random
from typing import List

from Block import Block
from Peer import Peer
from Piece import Piece


def read_peers_from_file(peers_file_path):
    """
    Read the peers ip and port from the peers file
    """
    peers = []

    with open(peers_file_path, 'rb') as peers_file:
        connections = peers_file.readlines()
        for connection in connections:
            ip, port = connection.decode().strip('\r\n').split(',')
            port = int(port)
            peer = Peer(ip=ip, port=port)

            peers.append(peer)

    return peers


def generate_peer_id():
    """
    Generate random peer id with length of 20 bytes
    """
    # TODO: generate peer id with program version
    return bytes([random.randint(0, 255) for i in range(20)])
