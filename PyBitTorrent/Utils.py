import random

from rich.console import Console

from PyBitTorrent.Peer import Peer

console = Console()


#
# def show_downloading_progress(pieces_manager: PieceManager, pieces_length: int):
#     written = 0
#     print("Starting the progress bar")
#     for _ in track(range(pieces_length), description=f"Dowloading"):
#         while True:
#             if pieces_manager.written > written:
#                 written = pieces_manager.written
#                 break
#     return
#     #
#     # while True:
#     #     if pieces_length <= pieces_manager.written:
#     #         print("Breaking")
#     #         return

def read_peers_from_file(peers_file):
    """
    Read the peers ip and port from the peers file
    """
    peers = []

    connections = peers_file.readlines()
    for connection in connections:
        ip, port = connection.decode().strip('\r\n').split(':')
        port = int(port)
        peer = Peer(ip=ip, port=port)

        peers.append(peer)

    peers_file.close()
    return peers


def generate_peer_id():
    """
    Generate random peer id with length of 20 bytes
    """
    # TODO: generate peer id with program version
    return bytes([random.randint(0, 255) for i in range(20)])
