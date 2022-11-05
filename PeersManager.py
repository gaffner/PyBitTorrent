import logging
from typing import List, Tuple

from Exceptions import PeerConnectionFailed, PeerHandshakeFailed, PeerDisconnected, OutOfPeers
from Message import Message
from Peer import Peer


class PeersManager:
    def __init__(self):
        self.peers: List[Peer] = []

    def add_peers(self, peers: List[Peer]):
        self.peers += peers

    def add_peer(self, peer: Peer):
        self.peers.append(peer)

    def send_handshake(self, my_id, info_hash):
        connected_peers = []
        for peer in self.peers:
            # Connect the peers
            try:
                peer.connect()
                connected_peers.append(peer)
            except PeerConnectionFailed:
                logging.getLogger('BitTorrent').info(f'Failed connecting to peer {peer}')
                continue

            # Handshake the peer
            try:
                peer.do_handshake(my_id, info_hash)
            except (PeerHandshakeFailed, PeerDisconnected):
                logging.getLogger('BitTorrent').info(f'Failed handshaking peer {peer}')
                self.peers.remove(peer)

        self.peers = connected_peers
        logging.getLogger('BitTorrent').info(f'Total peers connected: {len(self.peers)}')

    def receive_message(self) -> Tuple[Peer, Message]:
        """
        Receive new messages from clients
        """
        # select() goes here...

        ## FOR DEBUG ONLY:
        if len(self.peers) == 0:
            raise OutOfPeers

        peer = self.peers[0]
        # logging.getLogger('BitTorrent').debug(f'Choosing peer at index 0: {peer}')

        try:
            message = peer.receive_message()
        except PeerDisconnected:
            self.peers.remove(peer)
            return self.receive_message()

        return peer, message
