import logging
import math
import random
import select
import socket
import threading
from typing import List, Dict

from PyBitTorrent.Exceptions import PeerConnectionFailed, PeerDisconnected, OutOfPeers, NoPeersHavePiece, PeerHandshakeFailed, \
    AllPeersChocked
from PyBitTorrent.Message import MessageTypes
from PyBitTorrent.Peer import Peer

MAX_HANDSHAKE_THREADS = 80


class PeersManager:
    def __init__(self, max_peers):
        self.max_peers = max_peers
        self.peers: List[Peer] = []
        self.connected_peers: List[Peer] = []

    def add_peers(self, peers: List[Peer]):
        self.peers += peers

    def remove_peer(self, peer):
        # logging.getLogger('BitTorrent').debug(f'Removing peer {peer}')
        if peer in self.connected_peers:
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
            logging.getLogger('BitTorrent').debug(
                f"Adding peer {peer} which is {len(self.connected_peers)}/{self.max_peers}")

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

        for i in range(1, number_of_polls + 1):
            logging.getLogger('BitTorrent').debug(f'Poll number {i}/{number_of_polls}')
            poll = handshake_threads[:MAX_HANDSHAKE_THREADS]

            # Execute threads
            for thread in poll:
                thread.start()

            # Wait for them to finish
            for thread in poll:
                thread.join()

            if len(self.connected_peers) >= self.max_peers:
                logging.getLogger('BitTorrent').info(f'Reached max connected peers of {self.max_peers}')
                break

            # Slice the handshake threads
            del handshake_threads[:MAX_HANDSHAKE_THREADS]

        logging.getLogger('BitTorrent').info(f'Total peers connected: {len(self.connected_peers)}')

    def receive_messages(self) -> Dict[Peer, MessageTypes]:
        """
        Receive new messages from clients
        """
        # select() goes here...

        ## FOR DEBUG ONLY:
        if len(self.connected_peers) == 0:
            raise OutOfPeers

        # TODO: peer should inherit from socket, so just pass self.peers to select
        sockets = [peer.socket for peer in self.connected_peers]
        # print("Waiting for readables...")
        readables, _, _ = select.select(sockets, [], [])
        # print("done")
        # print("Readable:", readable)

        peers_to_message = {}
        for _peer in self.connected_peers:
            for readable in readables:
                if _peer.socket == readable:
                    peers_to_message[_peer] = None

        for peer in peers_to_message:
            try:
                message = peer.receive_message()
                peers_to_message[peer] = message
            except PeerDisconnected:
                logging.getLogger('BitTorrent').debug(f'Peer {peer} while waiting for message')
                self.remove_peer(peer)
                return self.receive_messages()

        # print("Messages length:", len(peers_to_message))
        return peers_to_message

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
