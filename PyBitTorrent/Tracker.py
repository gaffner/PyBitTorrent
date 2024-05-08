import socket
import struct
from abc import ABC, abstractmethod
from typing import List

from PyBitTorrent.Peer import Peer
from PyBitTorrent.TorrentFile import TorrentFile
from PyBitTorrent.Configuration import CONFIGURATION


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

        for _ in range(len(peers_bytes) // CONFIGURATION.compact_value_num_bytes):
            ip, port = struct.unpack_from("!iH", peers_bytes, offset)
            ip = socket.inet_ntoa(struct.pack("!i", ip))
            offset += CONFIGURATION.compact_value_num_bytes

            peers.append(Peer(ip, port))

        return peers
