import os
import random
import string
from importlib import metadata

from rich.console import Console

from PyBitTorrent.Peer import Peer

console = Console()


def read_peers_from_input(peers_input):

    peers = []
    if os.path.isfile(peers_input) :
        """
        Read the peers ip and port from the peers file
        """
        with open(peers_file_path, 'rb') as peers_file:
            connections = peers_file.readlines()

        for connection in connections:
            ip, port = connection.decode().strip("\r\n").split(":")
            port = int(port)
            peer = Peer(ip=ip, port=port)
            peers.append(peer)

    else :
        """
        Read the peers ip and port from string input delimited by commas
        """
        for peer in peers_input.split(","):
            ip, port = peer.split(":")
            peer = Peer(ip=ip, port=port)
            peers.append(peer)

    return peers


def generate_peer_id():
    """
    Generate random peer id with length of 20 bytes
    """
    try :
        version = metadata.version('PyBitTorrent').replace('.', '') + '0'
    except :
        version = "0000"
    id_suffix = ''.join([random.choice(string.ascii_letters) for _ in range(12)])
    peer_id = f'-GF{version}-{id_suffix}'
    assert len(peer_id) == 20

    return peer_id.encode()
