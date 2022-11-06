import hashlib
import logging
import random
import socket
from copy import deepcopy

import rich
from bcoding import bdecode, bencode

from Message import Handshake, KeepAlive, BitField, Unchoke
from PeersManager import PeersManager
from PiecesManager import PiecesManager
from TrackerFactory import TrackerFactory
from TrackerManager import TrackerManager
from Utils import read_peers_from_file

LISTENING_PORT = 6881
MAX_LISTENING_PORT = 6889


class BitTorrentClient:
    def __init__(self, torrent, peers_file=None):
        self.peer_manager: PeersManager = PeersManager()
        self.tracker_manager: TrackerManager
        self.id: bytes = BitTorrentClient.generate_peer_id()
        self.listener_socket: socket.socket = socket.socket()
        self.port: int = LISTENING_PORT
        self.should_continue: bool = True
        self.peers_file = peers_file
        self.piece_manager = None
        self.start_downloading = False

        # decode the config file and assign it
        logging.getLogger('BitTorrent').info('Start reading from BitTorrent file')
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
        self.start_listener()
        if self.peers_file:
            logging.getLogger('BitTorrent').info("Reading peers from file")
            peers = read_peers_from_file(self.peers_file)
        else:
            peers = self.tracker_manager.get_peers(self.id, self.port, self.config['info'])

        self.peer_manager.add_peers(peers)

        # Connect the peers
        self.peer_manager.send_handshake(self.id, self.info_hash)

        # initiate pieces manager
        self.piece_manager = PiecesManager(self.config['info']['length'], 16384,  # 16 KB
                                           self.peer_manager.peers)  # Passing peers to pieces manager is very ugly

        # Receive messages from peers
        self.handle_messages()

    def handle_messages(self):
        while self.should_continue:

            if self.start_downloading:
                self.piece_manager.request_piece()

            peer, message = self.peer_manager.receive_message()

            if type(message) is Handshake:
                peer.verify_handshake(message)

            elif type(message) is BitField:
                self.piece_manager.handle_bitfield(peer, message)  # TODO: why not recognize as message?

            elif type(message) is KeepAlive:
                logging.getLogger('BitTorrent').debug('Got keep alive')

            elif type(message) is Unchoke:
                peer.is_choked = False
                self.start_downloading = True

            else:
                logging.getLogger('BitTorrent').error(f'Unknown message: {message.id}')

    def status(self):
        pass

    @staticmethod
    def generate_peer_id():
        # TODO: generate peer id with program version
        return bytes([random.randint(0, 255) for i in range(20)])

    def start_listener(self):
        # TODO: make this actually works...

        current_port = LISTENING_PORT

        while current_port < MAX_LISTENING_PORT:
            try:
                self.listener_socket.bind(('', current_port))
                self.listener_socket.listen()
                break

            except OSError:
                logging.getLogger('BitTorrent').info(f'Failed to listen on port {current_port}')
                current_port += 1

        logging.getLogger('BitTorrent').info(f'Setting port to {current_port}')
        self.port = current_port
