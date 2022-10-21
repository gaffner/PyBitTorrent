import hashlib
import logging
from typing import Dict
from typing import List

import requests
from bcoding import bdecode, bencode

from Peer import Peer
from Tracker import Tracker


class HTTPTracker(Tracker):
    def get_peers(self, peer_id: bytes, port: int, info: Dict) -> List[Peer]:
        logging.getLogger('BitTorrent').error(f'Connecting to HTTP Tracker {self.url}')

        file_hash = hashlib.sha1(bencode(info)).digest()

        params = {'info_hash': file_hash,
                  'peer_id': peer_id, 'uploaded': 0,
                  'downloaded': 0, 'port': port, 'left': info['length'], 'event': 'started'}

        raw_response = requests.get(self.url, params=params).content
        tracker_response = bdecode(raw_response)
        peers = []

        if 'peers' in tracker_response.keys():
            peers = [Peer(info['ip'], info['port'], info['peer id']) for info in tracker_response['peers']]
        elif 'failure reason' in tracker_response():
            logging.getLogger('BitTorrent').error(
                f'Failure in tracker {self.url}: {tracker_response["failure reason"]}')
        else:
            logging.getLogger('BitTorrent').error(f'Unknown exception in tracker {self.url}')

        return peers
