from typing import List

from PyBitTorrent.Peer import Peer
from PyBitTorrent.TorrentFile import TorrentFile
from PyBitTorrent.Tracker import Tracker


class TrackerManager:
    def __init__(self, trackers: List[Tracker]):
        self.trackers: List[Tracker] = trackers

    def get_peers(
        self, peer_id: bytes, port: int, torrent_file: TorrentFile
    ) -> List[Peer]:
        """
        Return list of peers, by calling each tracker 'get_peer' method.
        This will cause a series of HTTP/UDP requests, in the end each
        one will return his list of peers.
        """
        peers = []
        for tracker in self.trackers:
            tracker_peers = tracker.get_peers(peer_id, port, torrent_file)
            peers += tracker_peers

        return peers
