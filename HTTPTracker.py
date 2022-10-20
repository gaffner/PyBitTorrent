import logging
import requests
from bcoding import bdecode

from Peer import Peer
from Tracker import Tracker


class HTTPTracker(Tracker):
    def get_peers(self):
        logging.getLogger('BitTorrent').error(f'Connecting to HTTP Tracker {self.url}')

        params = {'info_hash': b'\x8e\x90^\xa8\xe9%\xc3\xa7\xfd\xa9\xeb.\x96J\x0e\\\x97\xcc,\xe0',
                  'peer_id': b'\x02\x83s\xb0\x97\xf5h\x8f\x7f\xcdX\x87\xa7\x9f\xfd0~$\xe8B', 'uploaded': 0,
                  'downloaded': 0, 'port': 6881, 'left': 3767502848, 'event': 'started'}

        raw_response = requests.get(self.url, params=params).content
        tracker_response = bdecode(raw_response)
        tracker_peers = [Peer(info['ip'], info['port'], info['peer id']) for info in tracker_response['peers']]

        return tracker_peers
