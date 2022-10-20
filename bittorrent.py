from typing import Dict

from bcoding import bdecode

from peers_manager import PeersManager
from tracker_manager import TrackerManager


class BitTorrentClient:
    def __init__(self, torrent):
        self.config: Dict = {}
        self.peer_manager: PeersManager = PeersManager()
        self.tracker_manager: TrackerManager = TrackerManager()

        # Decode the config file and assign it
        torrent_data = torrent.read()
        self.config = bdecode(torrent_data)

    def start(self):
        pass

    def status(self):
        pass
