import logging
import random
import struct

DEFAULT_CONNECTION_ID = 0x41727101980
CONNECT = 0


class Connection:
    def __init__(self, transaction_id=None, connection_id=DEFAULT_CONNECTION_ID, action=CONNECT):
        self.transaction_id = transaction_id
        self.connection_id = connection_id
        self.action = action

        if transaction_id is None:
            self.transaction_id = random.randint(0, 65536)

    def __str__(self):
        return f'Transaction id: {self.transaction_id}, Connection id: {self.connection_id}, Action: {self.action}'

    def __eq__(self, other):
        return self.transaction_id == other.transaction_id

    def to_bytes(self):
        return struct.pack('>QII', self.connection_id, self.action, self.transaction_id)

    @staticmethod
    def from_bytes(payload):
        action, transaction_id, connection_id = struct.unpack('>IIQ', payload)
        return Connection(transaction_id=transaction_id, connection_id=connection_id, action=action)


class Announce:
    def __init__(self, connection_id, info_hash, peer_id, left, port, action=1, transaction_id=None):
        self.connection_id = connection_id
        self.transaction_id = transaction_id
        self.info_hash = info_hash
        self.left = left
        self.peer_id = peer_id
        self.port = port
        self.action = action

        if transaction_id is None:
            self.transaction_id = random.randint(0, 65536)

    def to_bytes(self):
        downloaded = 0
        left = 0
        uploaded = 0
        event = 0
        ip = 0
        key = 0
        num_want = -1

        _bytes = struct.pack('>QII20s20sQQQIIIiH', self.connection_id, self.action, self.transaction_id,
                             self.info_hash, self.peer_id, downloaded, left, uploaded, event, ip, key,
                             num_want, self.port)

        return _bytes


class AnnounceResult:
    def __init__(self, action, transaction_id, interval, leechers, seeders, peers=None):
        self.action = action
        self.transaction_id = transaction_id
        self.interval = interval
        self.leechers = leechers
        self.seeders = seeders
        self.peers = peers

    @staticmethod
    def from_bytes(payload):
        if len(payload) >= 20:
            return AnnounceResult(*struct.unpack('>IIIII', payload[:20]), payload[20:])
        else:
            return AnnounceResult(*struct.unpack('>II', payload[:8]), 0, 0, [])  # No peers
            logging.getLogger('BitTorrent').error("Tracker error:", payload[8:])
