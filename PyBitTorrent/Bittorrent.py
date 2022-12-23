import logging
import socket
import time
from threading import Thread
from typing import List

from rich import progress

from PyBitTorrent.Block import BlockStatus
from PyBitTorrent.Exceptions import PieceIsPending, NoPeersHavePiece, NoPieceFound, PeerDisconnected, PieceIsFull, OutOfPeers, \
    AllPeersChocked
from PyBitTorrent.PeersManager import PeersManager
from PyBitTorrent.Piece import Piece, create_pieces
from PyBitTorrent.PiecesManager import DiskManager
from PyBitTorrent import Utils
from PyBitTorrent.Message import (
    Handshake,
    KeepAlive,
    BitField,
    Unchoke,
    Request,
    PieceMessage,
    HaveMessage,
    Choke
)
from PyBitTorrent.TorrentFile import TorrentFile
from PyBitTorrent.TrackerFactory import TrackerFactory
from PyBitTorrent.TrackerManager import TrackerManager
from PyBitTorrent.Utils import generate_peer_id, read_peers_from_file

LISTENING_PORT = 6881
MAX_LISTENING_PORT = 6889
MAX_PEERS = 12
REQUEST_INTERVAL = 0.2


class BitTorrentClient:

    def __init__(self, torrent, max_peers=MAX_PEERS, no_progress_bar=False, peers_file=None):
        self.peer_manager: PeersManager = PeersManager(max_peers)
        self.tracker_manager: TrackerManager
        self.id: bytes = generate_peer_id()
        self.listener_socket: socket.socket = socket.socket()
        self.port: int = LISTENING_PORT
        self.peers_file = peers_file
        self.pieces: List[Piece] = []
        self.should_continue = True
        self.use_progress_bar = not no_progress_bar
        # decode the config file and assign it
        self.torrent = TorrentFile(torrent)
        self.piece_manager = DiskManager('{}.written'.format(self.torrent.file_name))
        # Utils.show_downloading_progress(None, None)
        # create tracker for each url of tracker in the config file
        trackers = []
        if 'announce' in self.torrent.config:
            tracker = TrackerFactory.create_tracker(self.torrent.config['announce'])
            trackers.append(tracker)

        if 'announce-list' in self.torrent.config:
            new_trackers = TrackerFactory.create_trackers(self.torrent.config['announce-list'])
            trackers += new_trackers

        self.tracker_manager = TrackerManager(trackers)
        file_size, piece_size = self.torrent.length, self.torrent.piece_size
        self.pieces = create_pieces(file_size, piece_size)
        self.number_of_pieces = len(self.pieces)

    def start(self):
        # Send HTTP/UDP Requests to all Trackers, requesting for peers

        if self.peers_file:
            logging.getLogger('BitTorrent').info("Reading peers from file")
            peers = read_peers_from_file(self.peers_file)
        else:
            peers = self.tracker_manager.get_peers(self.id, self.port, self.torrent)
            if len(peers) == 0:
                raise Exception("No peers found")

        logging.getLogger('BitTorrent').critical(f"Number of peers: {len(peers)}")

        self.peer_manager.add_peers(peers)
        handshakes = Thread(target=self.peer_manager.send_handshakes, args=(self.id, self.torrent.hash))
        requester = Thread(target=self.piece_requester)

        handshakes.start()
        requester.start()
        print("---------------------Done---------------------")
        self.progress_download()
        handshakes.join()
        requester.join()
        print("GoodBye!")

    def progress_download(self):
        if self.use_progress_bar:
            for _ in progress.track(range(len(self.pieces)), description=f"Downloading {self.torrent.file_name}"):
                self.handle_messages()
        else:
            for _ in range(len(self.pieces)):
                self.handle_messages()

    def handle_messages(self):
        while not self._all_pieces_full():
            try:
                # Utils.console.print(f'[purple]Waiting for message...')
                messages = self.peer_manager.receive_messages()
            except OutOfPeers:
                logging.getLogger('BitTorrent').error(f"No peers found, sleep for 2 seconds")
                time.sleep(2)
                continue
            except socket.error as e:
                logging.getLogger('BitTorrent').critical(f"Unknown socket error: {e}")
                continue

            for peer, message in messages.items():
                if type(message) is Handshake:
                    peer.verify_handshake(message)

                elif type(message) is BitField:
                    logging.getLogger('BitTorrent').info(f'Got bitfield from {peer}')
                    peer.set_bitfield(message)

                elif type(message) is HaveMessage:
                    peer.set_have(message)

                elif type(message) is KeepAlive:
                    logging.getLogger('BitTorrent').debug(f'Got keep alive from {peer}')

                elif type(message) is Choke:
                    print(f"Got choke from {peer}")
                    # Utils.console.print(f'[orange]Got choke from {peer} :(')
                    peer.set_choked()

                elif type(message) is Unchoke:
                    Utils.console.print(f'[red]Client unchoked {peer}')
                    peer.set_unchoked()

                elif type(message) is PieceMessage:
                    # print("Got piece!", message)
                    if self.handle_piece(message):
                        return

                else:
                    logging.getLogger('BitTorrent').error(f'Unknown message: {message.id}')  # should be error

    def piece_requester(self):
        """
        This function will run as different thread.
        Iterate over all the blocks of all the pieces
        in chronological order, and see if one of them is free.
        is yes - request it from random peer.
        """

        while self.should_continue:
            self.request_current_block()
            time.sleep(0.001)

        logging.getLogger('BitTorrent').critical(f'Exiting the requesting loop...')
        self.piece_manager.close()

    def request_current_block(self):
        for piece in self.pieces:
            try:
                block = piece.get_free_block()
                peer = self.peer_manager.get_random_peer_by_piece(piece)
                request = Request(piece.index, block.offset, block.size)
                peer.send_message(request)
                block.set_requested()
                return

            except PieceIsPending:
                # logging.getLogger('BitTorrent').debug(f'Piece {piece} is pending')
                continue

            except PieceIsFull:
                logging.getLogger('BitTorrent').debug(f'All blocks of piece {piece.index} are full, writing to disk...')
                continue

            except NoPeersHavePiece:
                logging.getLogger('BitTorrent').debug(f'No peers have piece {piece.index}')
                time.sleep(2.5)

            except AllPeersChocked:
                logging.getLogger('BitTorrent').debug(f'All of '
                                                      f'{len(self.peer_manager.connected_peers)} peers is chocked')
                time.sleep(2.5)

            except PeerDisconnected:
                logging.getLogger('BitTorrent').error(f'Peer {peer} disconnected when requesting for piece')
                self.peer_manager.remove_peer(peer)

        if self._all_pieces_full():
            self.should_continue = False

    def _all_pieces_full(self) -> bool:
        for piece in self.pieces:
            if not piece.is_full():
                return False

        return True

    def _get_piece_by_index(self, index):
        for piece in self.pieces:
            if piece.index == index:
                return piece

        raise NoPieceFound

    def handle_piece(self, pieceMessage: PieceMessage):
        try:
            if len(pieceMessage.data) == 0:
                print('Empty piece:', pieceMessage.index)
                return

            piece = self._get_piece_by_index(pieceMessage.index)
            block = piece.get_block_by_offset(pieceMessage.offset)
            block.data = pieceMessage.data
            block.status = BlockStatus.FULL
            # logging.getLogger('BitTorrent').debug(f'Successfully got some block of piece {piece.index}')
            # print("Got block of piece", pieceMessage.index)

            if piece.is_full():
                self.piece_manager.write_piece(piece, self.torrent.piece_size)
                self.pieces.remove(piece)
                if not self.use_progress_bar:
                    Utils.console.print(
                        "[green]Progress: {have}/{total} Unchoked peers: {peers_have}/{total_peers}".format(
                            have=self.piece_manager.written,
                            total=self.number_of_pieces, peers_have=self.peer_manager.num_of_unchoked,
                            total_peers=len(self.peer_manager.connected_peers)))

                del piece
                return True

        except PieceIsPending:
            logging.getLogger('BitTorrent').debug(f'Piece {pieceMessage.index} is pending')

        except NoPieceFound:
            # logging.getLogger('BitTorrent').debug(f'Piece {pieceMessage.index} not found')
            pass

        return False
