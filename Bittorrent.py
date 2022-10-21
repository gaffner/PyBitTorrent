import logging
import rich
from PeersManager import PeersManager
from TrackerFactory import TrackerFactory
from TrackerManager import TrackerManager
from bcoding import bdecode
from typing import Dict


class BitTorrentClient:
    def __init__(self, torrent):
        self.config: Dict = {}
        self.peer_manager: PeersManager = PeersManager()
        self.tracker_manager: TrackerManager
        self.peer_id: bytes = BitTorrentClient.generate_peer_id()

        # decode the config file and assign it
        logging.getLogger('BitTorrent').info('Start reading from BitTorrent file')
        torrent_data = torrent.read()
        self.config = bdecode(torrent_data)

        ## debug:
        config2 = self.config
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
        peers = self.tracker_manager.get_peers()
        self.peer_manager.add_peers(peers)

    def status(self):
        pass

    @staticmethod
    def generate_peer_id():
        # TODO: generate peer id with program version
        return bytes([random.randint(0, 255) for i in range(20)])

