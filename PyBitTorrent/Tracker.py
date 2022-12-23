import socket
import struct
from abc import ABC, abstractmethod
from typing import List

from PyBitTorrent.Peer import Peer
from PyBitTorrent.TorrentFile import TorrentFile

COMPACT_VALUE_NUM_BYTES = 6


class Tracker(ABC):
    def __init__(self, url):
        self.url = url

    @abstractmethod
    def get_peers(self, peer_id: bytes, port: int, torrent: TorrentFile) -> List[Peer]:
        pass

    @staticmethod
    def extract_compact_peers(peers_bytes) -> List[Peer]:
        offset = 0
        peers = []
        if not peers_bytes:
            return []

        for _ in range(len(peers_bytes) // COMPACT_VALUE_NUM_BYTES):
            ip, port = struct.unpack_from("!iH", peers_bytes, offset)[0]
            ip = socket.inet_ntoa(struct.pack("!i", ip))
            offset += 6

            peers.append(Peer(ip, port))

        return peers
