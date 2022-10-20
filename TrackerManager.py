from typing import List

from Peer import Peer
from Tracker import Tracker


class TrackerManager:
    def __init__(self, trackers: List[Tracker]):
        self.trackers: List[Tracker] = trackers

    def get_peers(self) -> List[Peer]:
        peers = []
        for tracker in self.trackers:
            tracker_peers = tracker.get_peers()
            peers += tracker_peers

        return peers
