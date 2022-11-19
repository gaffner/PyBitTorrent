# from Exceptions import NotSupported
import logging
from typing import Dict
from typing import List

from Peer import Peer
from TorrentFile import TorrentFile
from Tracker import Tracker


class UDPTracker(Tracker):
    def get_peers(self, peer_id: bytes, port: int, torrent: TorrentFile) -> List[Peer]:
        logging.getLogger('BitTorrent').error('No implementation to UDP tracker')
        # raise NotSupported

        return []
