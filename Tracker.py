import abc
from typing import Dict
from typing import List

from Peer import Peer


class Tracker(abc.ABC):
    def __init__(self, url):
        self.url = url

    def get_peers(self, peer_id: bytes, port: int, info: Dict) -> List[Peer]:
        pass
