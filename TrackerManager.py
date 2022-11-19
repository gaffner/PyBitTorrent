from typing import Dict
from typing import List

from Peer import Peer
from TorrentFile import TorrentFile
from Tracker import Tracker


class TrackerManager:
    def __init__(self, trackers: List[Tracker]):
        self.trackers: List[Tracker] = trackers

    def get_peers(self, peer_id: bytes, port: int, torrent_file: TorrentFile) -> List[Peer]:
        peers = []
        for tracker in self.trackers:
            tracker_peers = tracker.get_peers(peer_id, port, torrent_file)
            peers += tracker_peers

        return peers
