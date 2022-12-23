import socket
import struct
from abc import ABC, abstractmethod
from typing import List

from PyBitTorrent.Peer import Peer
from PyBitTorrent.TorrentFile import TorrentFile


class Tracker(ABC):
    def __init__(self, url):
        self.url = url

    @abstractmethod
    def get_peers(self, peer_id: bytes, port: int, torrent: TorrentFile) -> List[Peer]:
        pass

    @staticmethod
    def extract_compact_peers(peers_bytes) -> List[Peer]:
        # TODO: write new compact mode
        offset = 0
        peers = []
        if not peers_bytes:
            return []

        for _ in range(len(peers_bytes) // 6):
            ip = struct.unpack_from("!i", peers_bytes, offset)[0]
            ip = socket.inet_ntoa(struct.pack("!i", ip))
            offset += 4
            port = struct.unpack_from("!H", peers_bytes, offset)[0]
            offset += 2

            peers.append(Peer(ip, port))

        return peers
