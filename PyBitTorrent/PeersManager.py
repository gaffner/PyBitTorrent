import logging
import math
import random
import select
import socket
import threading
from typing import List, Dict

from PyBitTorrent.Exceptions import (
    PeerConnectionFailed,
    PeerDisconnected,
    OutOfPeers,
    NoPeersHavePiece,
    PeerHandshakeFailed,
    AllPeersChocked,
)
from PyBitTorrent.Message import MessageTypes
from PyBitTorrent.Peer import Peer

MAX_HANDSHAKE_THREADS = 80


class PeersManager:
    def __init__(self, max_peers):
        self.max_peers = max_peers
        self.peers: List[Peer] = []
        self.connected_peers: List[Peer] = []

    def add_peers(self, peers: List[Peer]):
        """
        Add peer to the list (still not connected)
        """
        self.peers += peers

    def remove_peer(self, peer):
        """
        Remove peer from the 'connected_peers' list.
        The reason why twin-like function not exists for the
        'peers' list resides in the fact we don't really care
        from this list, while we are very care form the connected_peers
        list, because we use in the receive_message function later.
        """
        if peer in self.connected_peers:
            self.connected_peers.remove(peer)

    def add_peer(self, peer: Peer):
        """
        Add peer to the list (still not connected)
        """
        self.peers.append(peer)

    def _send_handshake(self, my_id, info_hash, peer):
        """
        Send handshake to the given peer.
        NOTE: this function is BLOCKING.
        it waits until handshake response received, and failed otherwise.
        """
        logging.getLogger('BitTorrent').debug("Started: {}".format(threading.currentThread()))
        try:
            peer.connect()
        except PeerConnectionFailed:
            return
        try:
            # Send the handshake to peer
            logging.getLogger('BitTorrent').info(f'Trying handshake with peer {peer.ip}')

            peer.do_handshake(my_id, info_hash)

            # Consider it as connected client
            self.connected_peers.append(peer)

            logging.getLogger("BitTorrent").debug(
                f"Adding peer {peer} which is {len(self.connected_peers)}/{self.max_peers}"
            )

        except (PeerHandshakeFailed, PeerDisconnected, socket.error):
            pass

    def send_handshakes(self, my_id, info_hash):
        """
        Send handshake to all clients by create polls of threads
        That each one of them sending handshake to a constant number
        of peers. MAX_HANDSHAKE_THREADS decide the max peers to send
        handshake in each thread. big value will cause long run time
        for each thread and less threads, small value will cause for
        less run time to each thread and bigger number of threads.
        """
        # Create handshake thread for each peer
        handshake_threads = []
        for peer in self.peers:
            thread = threading.Thread(
                target=self._send_handshake, args=(my_id, info_hash, peer)
            )
            handshake_threads.append(thread)

        number_of_polls = int(len(handshake_threads) / MAX_HANDSHAKE_THREADS) + 1

        for i in range(1, number_of_polls + 1):
            logging.getLogger("BitTorrent").debug(f"Poll number {i}/{number_of_polls}")
            poll = handshake_threads[:MAX_HANDSHAKE_THREADS]

            # Execute threads
            for thread in poll:
                thread.start()

            # Wait for them to finish
            for thread in poll:
                thread.join()

            if len(self.connected_peers) >= self.max_peers:
                logging.getLogger("BitTorrent").info(
                    f"Reached max connected peers of {self.max_peers}"
                )
                break

            # Slice the handshake threads
            del handshake_threads[:MAX_HANDSHAKE_THREADS]

        logging.getLogger("BitTorrent").info(
            f"Total peers connected: {len(self.connected_peers)}"
        )

    def receive_messages(self) -> Dict[Peer, MessageTypes]:
        """
        Receive new messages from clients
        """

        # First, check if we out of peers
        if len(self.connected_peers) == 0:
            raise OutOfPeers

        # Check for new readable sockets from the connected peers
        sockets = [peer.socket for peer in self.connected_peers]
        readable, _, _ = select.select(sockets, [], [])

        peers_to_message = {}
        # Extract peer from given sockets
        for _peer in self.connected_peers:
            for readable in readable:
                if _peer.socket == readable:
                    peers_to_message[_peer] = None

        # Receive messages from all the given peers
        for peer in peers_to_message:
            try:
                message = peer.receive_message()
                peers_to_message[peer] = message
            except PeerDisconnected:
                logging.getLogger("BitTorrent").debug(
                    f"Peer {peer} while waiting for message"
                )
                self.remove_peer(peer)
                return self.receive_messages()

        return peers_to_message

    def get_random_peer_by_piece(self, piece):
        """
        Get random peer having the given piece
        Will check at the beginning if all peers are choked,
        And choose randomly one of the peers that have the
        piece (By looking at each peer bitfiled).
        """
        peers_have_piece = []

        # Check if all the peers choked
        all_is_chocked = math.prod([peer.is_choked for peer in self.connected_peers])
        if all_is_chocked:
            raise AllPeersChocked  # If they are, then even if they have the piece it's not relevant

        # Check from all the peers who have the piece
        for peer in self.connected_peers:
            if peer.have_piece(piece) and not peer.is_choked:
                peers_have_piece.append(peer)

        # If we left with any peers, shuffle from them
        if peers_have_piece:
            return random.choice(peers_have_piece)

        # If we reached so far... then no peer founded
        raise NoPeersHavePiece

    @property
    def num_of_unchoked(self):
        """
        Count the number of unchoked peers
        """
        count = 0
        for peer in self.connected_peers:
            if not peer.is_choked:
                count += 1

        return count
