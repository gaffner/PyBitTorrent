from typing import List, Optional

from Peer import Peer


class PeersManager:
    def __init__(self):
        self.peers: List[Peer] = []

    def add_peers(self, peers: List[Peer]):
        self.peers += peers

    def add_peer(self, peer: Peer):
        self.peers.append(peer)
