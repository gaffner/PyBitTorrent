import logging
import math
import random
import select
import socket
import threading
from typing import List, Tuple

from Exceptions import PeerConnectionFailed, PeerDisconnected, OutOfPeers, NoPeersHavePiece, PeerHandshakeFailed, \
    AllPeersChocked
from Message import MessageTypes
from Peer import Peer

MAX_CONNECTED_PEERS = 40  # we are doing this because in the current status we are doing sync-check of the sockets
MAX_HANDSHAKE_THREADS = 80


class PeersManager:
    def __init__(self):
        self.peers: List[Peer] = []
        self.connected_peers: List[Peer] = []

    def add_peers(self, peers: List[Peer]):
        self.peers += peers

    def remove_peer(self, peer):
        # logging.getLogger('BitTorrent').debug(f'Removing peer {peer}')
        if peer in self.peers:
            self.connected_peers.remove(peer)

    def add_peer(self, peer: Peer):
        self.peers.append(peer)

    def _send_handshake(self, my_id, info_hash, peer):
        # print("Started: {}".format(threading.currentThread()))
        try:
            peer.connect()
        except PeerConnectionFailed:
            # logging.getLogger('BitTorrent').info(f'Failed connecting to peer {peer}')
            return
        try:
            # Send the handshake to peer
            # logging.getLogger('BitTorrent').info(f'Trying handshake with peer {peer.ip}')

            peer.do_handshake(my_id, info_hash)

            # Consider it as connected client
            self.connected_peers.append(peer)

            # logging.getLogger('BitTorrent').info(f'Success in handshaking peer {peer}')
            print(f"Adding peer {peer} which is {len(self.connected_peers)}/{MAX_CONNECTED_PEERS}")

        except (PeerHandshakeFailed, PeerDisconnected, socket.error):
            # logging.getLogger('BitTorrent').debug(f'Failed handshaking peer {peer}')
            pass

    def send_handshakes(self, my_id, info_hash):
        # Create handshake thread for each peer
        handshake_threads = []
        for peer in self.peers:
            thread = threading.Thread(target=self._send_handshake, args=(my_id, info_hash, peer))
            handshake_threads.append(thread)

        number_of_polls = int(len(handshake_threads) / MAX_HANDSHAKE_THREADS) + 1
        #
        # number_of_polls = 5
        # if number_of_polls * MAX_HANDSHAKE_THREADS > len(handshake_threads):
        #     number_of_polls = int(len(handshake_threads) / MAX_HANDSHAKE_THREADS) + 1

        for i in range(1, number_of_polls):
            logging.getLogger('BitTorrent').debug(f'Poll number {i}/{number_of_polls}')
            poll = handshake_threads[:MAX_HANDSHAKE_THREADS]

            # Execute threads
            for thread in poll:
                thread.start()

            # Wait for them to finish
            for thread in poll:
                thread.join()

            if len(self.connected_peers) >= MAX_CONNECTED_PEERS:
                logging.getLogger('BitTorrent').info(f'Reached max connected peers of {MAX_CONNECTED_PEERS}')
                break

            # Slice the handshake threads
            del handshake_threads[:MAX_HANDSHAKE_THREADS]

        logging.getLogger('BitTorrent').info(f'Total peers connected: {len(self.connected_peers)}')
        if len(self.connected_peers) == 0:
            raise OutOfPeers

    def receive_message(self) -> Tuple[Peer, MessageTypes]:
        """
        Receive new messages from clients
        """
        # select() goes here...

        ## FOR DEBUG ONLY:
        if len(self.connected_peers) == 0:
            raise OutOfPeers

        # TODO: peer should inherit from socket, so just pass self.peers to select
        sockets = [peer.socket for peer in self.connected_peers]
        readable, _, _ = select.select(sockets, [], [])

        peer = None
        for _peer in self.connected_peers:
            if _peer.socket == readable[0]:
                peer = _peer

        if not peer:
            raise NotImplemented

        # logging.getLogger('BitTorrent').debug(f'Choosing peer at index 0: {peer}')

        try:
            message = peer.receive_message()
        except PeerDisconnected:
            logging.getLogger('BitTorrent').debug(f'Peer {peer} while waiting for message')
            self.remove_peer(peer)
            return self.receive_message()

        return peer, message

    def get_random_peer_by_piece(self, piece):
        peers_have_piece = []

        for peer in self.connected_peers:
            if peer.have_piece(piece) and not peer.is_choked:
                peers_have_piece.append(peer)

        all_is_chocked = math.prod([peer.is_choked for peer in self.connected_peers])
        if all_is_chocked:
            raise AllPeersChocked

        if peers_have_piece:
            return random.choice(peers_have_piece)

        raise NoPeersHavePiece

    @property
    def num_of_unchoked(self):
        count = 0
        for peer in self.connected_peers:
            if not peer.is_choked:
                count += 1

        return count
