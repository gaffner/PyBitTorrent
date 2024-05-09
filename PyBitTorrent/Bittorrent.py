import logging
import socket
import time
from threading import Thread
from typing import List

from rich import progress

from PyBitTorrent import Utils
from PyBitTorrent.Block import BlockStatus
from PyBitTorrent.Exceptions import (
    PieceIsPending,
    NoPeersHavePiece,
    NoPieceFound,
    PeerDisconnected,
    PieceIsFull,
    OutOfPeers,
    AllPeersChocked,
)
from PyBitTorrent.Message import (
    Handshake,
    KeepAlive,
    BitField,
    Unchoke,
    Request,
    PieceMessage,
    HaveMessage,
    Choke,
)
from PyBitTorrent.PeersManager import PeersManager
from PyBitTorrent.Piece import Piece, create_pieces
from PyBitTorrent.PiecesManager import DiskManager
from PyBitTorrent.TorrentFile import TorrentFile
from PyBitTorrent.TrackerFactory import TrackerFactory
from PyBitTorrent.TrackerManager import TrackerManager
from PyBitTorrent.Utils import generate_peer_id, read_peers_from_input
from PyBitTorrent.Exceptions import NoTrackersFound
from PyBitTorrent.Configuration import CONFIGURATION

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )


class TorrentClient:
    def __init__(
            self, torrent: str,
            max_peers: int = CONFIGURATION.max_peers,
            use_progress_bar: bool = True,
            peers_input: str = None,
            output_dir: str = '.'
    ):
        self.peer_manager: PeersManager = PeersManager(max_peers)
        self.tracker_manager: TrackerManager
        self.id: bytes = generate_peer_id()
        self.listener_socket: socket.socket = socket.socket()
        self.listener_socket.settimeout(CONFIGURATION.timeout)
        self.port: int = CONFIGURATION.listening_port
        self.peers_input: str = peers_input
        self.pieces: List[Piece] = []
        self.should_continue = True
        self.use_progress_bar = use_progress_bar
        if use_progress_bar:
            logging.getLogger("BitTorrent").setLevel(CONFIGURATION.logging_level)

        # decode the config file and assign it
        self.torrent = TorrentFile(torrent)
        self.piece_manager = DiskManager(output_dir, self.torrent)
        # create tracker for each url of tracker in the config file
        trackers = []
        if "announce" in self.torrent.config:
            tracker = TrackerFactory.create_tracker(self.torrent.config["announce"])
            trackers.append(tracker)

        if "announce-list" in self.torrent.config:
            new_trackers = TrackerFactory.create_trackers(
                self.torrent.config["announce-list"]
            )
            trackers += new_trackers

        while None in trackers:
            trackers.remove(None)

        if len(trackers) == 0:
            raise NoTrackersFound

        self.tracker_manager = TrackerManager(trackers)
        file_size, piece_size = self.torrent.length, self.torrent.piece_size
        self.pieces = create_pieces(file_size, piece_size)
        self.number_of_pieces = len(self.pieces)

    def setup(self):
        # Send HTTP/UDP Requests to all Trackers, requesting for peers
        if self.peers_input:
            logging.getLogger("BitTorrent").info("Reading peers from input")
            peers = read_peers_from_input(self.peers_input)
        else:
            peers = self.tracker_manager.get_peers(self.id, self.port, self.torrent)
            if len(peers) == 0:
                raise Exception("No peers found")

        logging.getLogger("BitTorrent").info(f"Number of peers: {len(peers)}")

        self.peer_manager.add_peers(peers)

    def start(self):
        if len(self.peer_manager.peers) == 0:
            self.setup()

        handshakes = Thread(
            target=self.peer_manager.send_handshakes, args=(self.id, self.torrent.hash)
        )
        requester = Thread(target=self.piece_requester)

        handshakes.start()
        requester.start()
        self.progress_download()
        handshakes.join()
        requester.join()
        Utils.console.print("[green]GoodBye!")

    def progress_download(self):
        if self.use_progress_bar:
            for _ in progress.track(
                    range(len(self.pieces)),
                    description=f"Downloading {self.torrent.file_name}",
            ):
                self.handle_messages()
        else:
            for _ in range(len(self.pieces)):
                self.handle_messages()

    def handle_messages(self):
        while not self._all_pieces_full():
            try:
                # Utils.console.print.f'[purple]Waiting for message...')
                messages = self.peer_manager.receive_messages()
            except OutOfPeers:
                logging.getLogger("BitTorrent").error(
                    f"No peers found, sleep for 2 seconds"
                )
                time.sleep(2)
                continue
            except socket.error as e:
                logging.getLogger("BitTorrent").info(f"Unknown socket error: {e}")
                continue

            for peer, message in messages.items():
                if type(message) is Handshake:
                    peer.verify_handshake(message)

                elif type(message) is BitField:
                    logging.getLogger("BitTorrent").info(f"Got bitfield from {peer}")
                    peer.set_bitfield(message)

                elif type(message) is HaveMessage:
                    peer.set_have(message)

                elif type(message) is KeepAlive:
                    logging.getLogger("BitTorrent").debug(f"Got keep alive from {peer}")

                elif type(message) is Choke:
                    peer.set_choked()

                elif type(message) is Unchoke:
                    logging.getLogger("BitTorrent").debug(f"Received unchoke from {peer}")
                    peer.set_unchoked()

                elif type(message) is PieceMessage:
                    # "Got piece!", message)
                    if self.handle_piece(message):
                        return

                else:
                    logging.getLogger("BitTorrent").error(
                        f"Unknown message: {message.id}"
                    )  # should be error

    def piece_requester(self):
        """
        This function will run as different thread.
        Iterate over all the blocks of all the pieces
        in chronological order, and see if one of them is free.
        is yes - request it from random peer.
        """

        while self.should_continue:
            self.request_current_block()
            time.sleep(CONFIGURATION.iteration_sleep_interval)

        logging.getLogger("BitTorrent").info(f"Exiting the requesting loop...")
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
                continue

            except PieceIsFull:
                continue

            except NoPeersHavePiece:
                logging.getLogger("BitTorrent").debug(
                    f"No peers have piece {piece.index}"
                )
                time.sleep(2.5)

            except AllPeersChocked:
                logging.getLogger("BitTorrent").debug(
                    f"All of "
                    f"{len(self.peer_manager.connected_peers)} peers is chocked"
                )
                time.sleep(2.5)

            except PeerDisconnected:
                logging.getLogger("BitTorrent").error(
                    f"Peer {peer} disconnected when requesting for piece"
                )
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
            if not len(pieceMessage.data):
                logging.getLogger("BitTorrent").debug("Empty piece:", pieceMessage.index)
                return

            piece = self._get_piece_by_index(pieceMessage.index)
            block = piece.get_block_by_offset(pieceMessage.offset)
            block.data = pieceMessage.data
            block.status = BlockStatus.FULL

            if piece.is_full():
                self.piece_manager.write_piece(piece, self.torrent.piece_size)
                self.pieces.remove(piece)
                if not self.use_progress_bar:
                    logging.getLogger("BitTorrent").info(
                        "Progress: {have}/{total} Unchoked peers: {peers_have}/{total_peers}".format(
                            have=self.piece_manager.written,
                            total=self.number_of_pieces,
                            peers_have=self.peer_manager.num_of_unchoked,
                            total_peers=len(self.peer_manager.connected_peers),
                        )
                    )

                del piece
                return True

        except PieceIsPending:
            logging.getLogger("BitTorrent").debug(
                f"Piece {pieceMessage.index} is pending"
            )

        except NoPieceFound:
            pass

        return False
