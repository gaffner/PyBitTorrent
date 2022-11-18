import logging
import random
import select
from typing import List, Tuple

from Exceptions import PeerConnectionFailed, PeerHandshakeFailed, PeerDisconnected, OutOfPeers, NoPeersHavePiece
from Message import MessageTypes
from Peer import Peer


class PeersManager:
    def __init__(self):
        self.peers: List[Peer] = []

    def add_peers(self, peers: List[Peer]):
        self.peers += peers

    def remove_peer(self, peer):
        self.peers.remove(peer)

    def add_peer(self, peer: Peer):
        self.peers.append(peer)

    def send_handshake(self, my_id, info_hash):
        connected_peers = []
        for peer in self.peers:
            # Connect the peers
            try:
                peer.connect()
                connected_peers.append(peer)
                logging.getLogger('BitTorrent').info(f'Success in connecting to peer {peer}')
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

    def receive_message(self) -> Tuple[Peer, MessageTypes]:
        """
        Receive new messages from clients
        """
        # select() goes here...

        ## FOR DEBUG ONLY:
        if len(self.peers) == 0:
            raise OutOfPeers

        # TODO: peer should inherit from socket, so just pass self.peers to select
        sockets = [peer.socket for peer in self.peers]
        readable, _, _ = select.select(sockets, [], [])

        peer = None
        for _peer in self.peers:
            if _peer.socket == readable[0]:
                peer = _peer

        if not peer:
            raise NotImplemented

        # logging.getLogger('BitTorrent').debug(f'Choosing peer at index 0: {peer}')

        try:
            message = peer.receive_message()
        except PeerDisconnected:
            self.peers.remove(peer)
            return self.receive_message()

        return peer, message

    def get_random_peer_by_piece(self, piece):
        peers_have_piece = []
        for peer in self.peers:
            if peer.have_piece(piece):
                peers_have_piece.append(peer)

        if peers_have_piece:
            return random.choice(peers_have_piece)

        raise NoPeersHavePiece
