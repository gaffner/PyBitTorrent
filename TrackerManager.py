from typing import List

from Peer import Peer
from Tracker import Tracker


class TrackerManager:
    def __init__(self, trackers: List[Tracker]):
        self.trackers: List[Tracker] = trackers

    def get_peers(self, file_hash, peer_id) -> List[Peer]:
        peers = []
        for tracker in self.trackers:
            tracker_peers = tracker.get_peers(file_hash, peer_id)
            peers += tracker_peers

        return peers
