import hashlib
import logging
import socket
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
        self.have_all_pieces = False
        self.piece_manager = PieceManager('test.bin')
        self.written_pieces_length = 0
        # decode the config file and assign it
        logging.getLogger('BitTorrent').critical('Start reading from BitTorrent file')
        torrent_data = torrent.read()
        self.config = bdecode(torrent_data)
        self.info_hash = hashlib.sha1(bencode(self.config['info'])).digest()

        ## debug:
        config2 = deepcopy(self.config)
        config2['info']['pieces'] = ''
        rich.print(config2)

        # create tracker for each tracker url in the config file
        trackers = []
        if 'announce' in self.config.keys():
            tracker = TrackerFactory.create_tracker(self.config['announce'])
            trackers.append(tracker)

        if 'announce-list' in self.config.keys():
            new_trackers = TrackerFactory.create_trackers(self.config['announce-list'])
            trackers += new_trackers

        self.tracker_manager = TrackerManager(trackers)

    def start(self):
        # Send HTTP/UDP Requests to all Trackers, requesting for peers

        if self.peers_file:
            logging.getLogger('BitTorrent').info("Reading peers from file")
            peers = read_peers_from_file(self.peers_file)
        else:
            peers = self.tracker_manager.get_peers(self.id, self.port, self.config['info'])

        self.peer_manager.add_peers(peers)
        self.peer_manager.send_handshake(self.id, self.info_hash)  # Connect the peers

        requester = Thread(target=self.piece_requester)
        requester.start()

        self.handle_messages()

    def handle_messages(self):
        while True:
            peer, message = self.peer_manager.receive_message()

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

        file_size, piece_size = self.config['info']['length'], self.config['info']['piece length']
        self.pieces = create_pieces(file_size, piece_size)

        while not self.have_all_pieces:
            self.request_current_block()
            time.sleep(REQUEST_INTERVAL)

        logging.getLogger('BitTorrent').critical(f'Finish downloading all pieces, saving to file')
        logging.getLogger('BitTorrent').critical(f'GoodBye!')

    def request_current_block(self):
        for piece in self.pieces:
            try:
                block = piece.get_free_block()
                peer = self.peer_manager.get_random_peer_by_piece(piece)
                request = Request(piece.index, block.offset, block.size)
                peer.send_message(request)
                return

            except PieceIsPending:
                logging.getLogger('BitTorrent').info(f'Piece {piece} is pending')

            except PieceIsFull:
                logging.getLogger('BitTorrent').info(f'All blocks of piece {piece.index} are full, writing to disk...')

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
                logging.getLogger('BitTorrent').info(f'No peers have piece {piece.index}')

            except PeerDisconnected:
                logging.getLogger('BitTorrent').info(f'Peer {peer} disconnected when requesting for piece')
                self.peer_manager.remove_peer(peer)

        self.have_all_pieces = True

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
            logging.getLogger('BitTorrent').info(f'Successfully got block {block.offset} of piece {piece.index}')

        except (NoPieceFound, PieceIsPending):
            logging.getLogger('BitTorrent').info(f'Failed to process block or piece of {pieceMessage.index}')
