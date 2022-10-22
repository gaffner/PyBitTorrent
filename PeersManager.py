import logging
from typing import List, Tuple

from Exceptions import PeerConnectionFailed, PeerHandshakeFailed
from Message import Message
from Peer import Peer


class PeersManager:
    def __init__(self):
        self.peers: List[Peer] = []

    def add_peers(self, peers: List[Peer]):
        self.peers += peers

    def add_peer(self, peer: Peer):
        self.peers.append(peer)

    def do_handshake(self):
        for peer in self.peers:
            # Connect the peers
            try:
                peer.connect()
            except PeerConnectionFailed:
                logging.getLogger('BitTorrent').info(f'Failed connecting to peer {peer}')
                self.peers.remove(peer)

            # Handshake the peer
            try:
                peer.handshake()
            except PeerHandshakeFailed:
                logging.getLogger('BitTorrent').info(f'Failed handshaking peer {peer}')
                self.peers.remove(peer)

        logging.getLogger('BitTorrent').info(f'Total peers connected: {len(self.peers)}')

    def receive_message(self) -> Tuple[Peer, Message]:
        """
        Receive new messages from clients
        """
        ## FOR DEBUG ONLY:
        peer = self.peers[0]
        logging.getLogger('BitTorrent').debug(f'Choosing peer at index 1: {peer}')

        message = peer.receive_message()
        return peer, message