import hashlib
import logging
import socket
import struct
import time
from copy import deepcopy
from threading import Thread
from typing import List

import rich
from bcoding import bdecode, bencode

from Block import BlockStatus
from Exceptions import PieceIsPending, NoPeersHavePiece, NoPieceFound, PeerDisconnected, PieceIsFull
from Message import Handshake, KeepAlive, BitField, Unchoke, Request, PieceMessage
from PeersManager import PeersManager
from Piece import Piece, create_pieces
from PiecesManager import PieceManager
from TrackerFactory import TrackerFactory
from TrackerManager import TrackerManager
from Utils import generate_peer_id, read_peers_from_file

from TorrentFile import TorrentFile

LISTENING_PORT = 6881
MAX_LISTENING_PORT = 6889
REQUEST_INTERVAL = 0.2


class BitTorrentClient:

    def __init__(self, torrent, peers_file=None):
        self.peer_manager: PeersManager = PeersManager()
        self.tracker_manager: TrackerManager
        self.id: bytes = generate_peer_id()
        self.listener_socket: socket.socket = socket.socket()
        self.port: int = LISTENING_PORT
        self.peers_file = peers_file
        self.pieces: List[Piece] = []
        self.should_continue = True
        self.piece_manager = PieceManager('test2.bin')  # TODO: change to real file name
        self.written_pieces_length = 0
        # decode the config file and assign it
        self.torrent = TorrentFile(torrent)

        # create tracker for each url of tracker in the config file
        trackers = []
        if 'announce' in self.torrent.config:
            tracker = TrackerFactory.create_tracker(self.torrent.config['announce'])
            trackers.append(tracker)

        if 'announce-list' in self.torrent.config:
            new_trackers = TrackerFactory.create_trackers(self.torrent.config['announce-list'])
            trackers += new_trackers

        self.tracker_manager = TrackerManager(trackers)

    def start(self):
        # Send HTTP/UDP Requests to all Trackers, requesting for peers

        if self.peers_file:
            logging.getLogger('BitTorrent').info("Reading peers from file")
            peers = read_peers_from_file(self.peers_file)
        else:
            peers = self.tracker_manager.get_peers(self.id, self.port, self.torrent)
            if len(peers) == 0:
                raise Exception("No peers found")

        logging.getLogger('BitTorrent').critical(f"Rumber of connected peers: {len(peers)}")
        if len(peers) > 20:
            peers = peers[:20]
            print('Cutting peers')

        self.peer_manager.add_peers(peers)
        self.peer_manager.send_handshake(self.id, self.torrent.hash)  # Connect the peers

        requester = Thread(target=self.piece_requester)
        requester.start()

        self.handle_messages()

    def handle_messages(self):
        while True:
            try:
                peer, message = self.peer_manager.receive_message()
            except struct.error as e:
                logging.getLogger('BitTorrent').critical(f'error: {e}')

            if type(message) is Handshake:
                peer.verify_handshake(message)

            elif type(message) is BitField:
                logging.getLogger('BitTorrent').info(f'Got bitfield from {peer}')
                peer.set_bitfield(message)

            elif type(message) is KeepAlive:
                logging.getLogger('BitTorrent').debug(f'Got keep alive from {peer}')

            elif type(message) is Unchoke:
                logging.getLogger('BitTorrent').info(f'Got unchoke from {peer}')
                peer.set_unchoke(Unchoke)

            elif type(message) is PieceMessage:
                self.handle_piece(message)

            else:
                logging.getLogger('BitTorrent').debug(f'Unknown message: {message.id}')  # should be error

    def piece_requester(self):
        """
        This function will run as different thread.
        Iterate over all the blocks of all the pieces
        in chronological order, and see if one of them is free.
        is yes - request it from random peer.
        """

        file_size, piece_size = self.torrent.length, self.torrent.piece_size
        self.pieces = create_pieces(file_size, piece_size)

        while self.should_continue:
            self.request_current_block()
            time.sleep(REQUEST_INTERVAL)

        logging.getLogger('BitTorrent').critical(f'Exiting the requesting loop...')
        self.piece_manager.close()

    def request_current_block(self):
        for piece in self.pieces:
            try:
                block = piece.get_free_block()
                peer = self.peer_manager.get_random_peer_by_piece(piece)
                request = Request(piece.index, block.offset, block.size)
                peer.send_message(request)
                return

            except PieceIsPending:
                logging.getLogger('BitTorrent').debug(f'Piece {piece} is pending')

            except PieceIsFull:
                logging.getLogger('BitTorrent').critical(f'All blocks of piece {piece.index} are full, writing to disk...')

                self.piece_manager.write_piece(piece)
                self.pieces.remove(piece)
                self.written_pieces_length += 1
                del piece

                percentage_completed = (self.written_pieces_length / len(self.pieces)) * 100
                logging.getLogger('BitTorrent').critical("Connected peers: {} - {}% completed | {}/{} pieces"
                                                         .format(len(self.peer_manager.peers), percentage_completed,
                                                                 self.written_pieces_length, len(self.pieces)))
                return

            except NoPeersHavePiece:
                logging.getLogger('BitTorrent').critical(f'No peers have piece {piece.index}')

            except PeerDisconnected:
                logging.getLogger('BitTorrent').info(f'Peer {peer} disconnected when requesting for piece')
                self.peer_manager.remove_peer(peer)

        self.should_continue = False

    def _get_piece_by_index(self, index):
        for piece in self.pieces:
            if piece.index == index:
                return piece

        raise NoPieceFound

    def handle_piece(self, pieceMessage: PieceMessage):
        try:
            piece = self._get_piece_by_index(pieceMessage.index)
            block = piece.get_block_by_offset(pieceMessage.offset)
            block.status = BlockStatus.FULL
            block.data = pieceMessage.data
            logging.getLogger('BitTorrent').info(f'Successfully got block {block.offset} of piece {piece.index}')

        except (NoPieceFound, PieceIsPending):
            logging.getLogger('BitTorrent').info(f'Failed to process block or piece of {pieceMessage.index}')
