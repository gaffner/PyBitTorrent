import hashlib
import logging
import socket
import struct
from typing import List, Dict

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

        try:
            raw_response = requests.get(self.url, params=params).content
        except requests.exceptions.ConnectionError:
            logging.getLogger('BitTorrent').error(f'Failed connecting to tracker {self.url}')
            return []
        tracker_response = bdecode(raw_response)
        print(tracker_response)
        peers = []

        if 'peers' in tracker_response.keys():
            peers_list = tracker_response['peers']
            if type(peers_list) == bytes:
                peers = HTTPTracker.decrypt_compact_answer(peers_list)
            else:
                peers = [Peer(info['ip'], info['port'], info['peer id']) for info in peers_list]
        elif 'failure reason' in tracker_response():
            logging.getLogger('BitTorrent').error(
                f'Failure in tracker {self.url}: {tracker_response["failure reason"]}')
        else:
            logging.getLogger('BitTorrent').error(f'Unknown exception in tracker {self.url}')

        return peers

    @staticmethod
    def decrypt_compact_answer(peers_bytes) -> List[Peer]:
        # TODO: write my own compact mode function
        offset = 0
        peers = []

        for _ in range(len(peers_bytes) // 6):
            ip = struct.unpack_from("!i", peers_bytes, offset)[0]
            ip = socket.inet_ntoa(struct.pack("!i", ip))
            offset += 4
            port = struct.unpack_from("!H", peers_bytes, offset)[0]
            offset += 2

            peers.append(Peer(ip, port))

        return peers
