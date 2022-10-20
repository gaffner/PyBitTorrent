from typing import List

from peer import Peer


class PeersManager:
    def __init__(self):
        self.peers: List[Peer] = []
