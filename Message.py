import struct

HANDSHAKE = 0


class Message:
    def __init__(self, _id):
        self.id = _id


class UnknownMessage(Message):
    pass


class Handshake(Message):
    def __init__(self, peer_id: bytes, info_hash: bytes, protocol: str = 'BitTorrent protocol'):
        super().__init__(HANDSHAKE)
        self.peer_id = peer_id
        self.info_hash = info_hash
        self.protocol = protocol

    def to_bytes(self) -> bytes:
        protocol_len = len(self.protocol)
        handshake = struct.pack(f'>B{protocol_len}s8s20s20s',
                                protocol_len,
                                self.protocol.encode(),
                                b'\x00' * 8,
                                self.info_hash,
                                self.peer_id)

        return handshake

    @staticmethod
    def from_bytes(payload: bytes):
        protocol_len = struct.unpack('>B', payload[:1])[0]
        protocol, reserved, info_hash, peer_id = struct.unpack(f'>{protocol_len}s8s20s20s', payload[1:])

        return Handshake(peer_id, info_hash, protocol)

    def __eq__(self, other):
        return self.info_hash == other.info_hash


class Request(Message):
    pass


class Piece(Message):
    pass
