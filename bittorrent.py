from peers_manager import PeersManager
from tracker_manager import TrackerManager


class BitTorrentClient:
    def __init__(self, torrent_file_path):
        self.torrent_file = open(torrent_file_path, 'rb')
        self.peer_manager: PeersManager = None
        self.tracker_manager: TrackerManager = None

    def start(self):
        pass

    def status(self):
        pass
