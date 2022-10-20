from typing import List

from peer import Peer
from tracker import Tracker


class TrackerManager:
    def __init__(self):
        self.trackers: List[Tracker] = []

    def get_peers(self) -> List[Peer]:
        pass
