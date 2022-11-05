import enum
import struct
from abc import ABC, abstractmethod

from bitstring import BitArray


class MessageCode(enum.IntEnum):
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7
    CANCEL = 8
    PORT = 9

    HANDSHAKE = -1


class Message(ABC):

    @abstractmethod
    def to_bytes(self) -> bytes:
        pass

    @staticmethod
    @abstractmethod
    def from_bytes(payload):
        pass


class Request(Message):
    def __init__(self, index, begin, length):
        self.id = MessageCode.REQUEST
        self.index = index  # 4 byte
        self.begin = begin  # 4 bytes
        self.length = length  # 4 bytes
        self.total_length = 13  # bytes

    def to_bytes(self) -> bytes:
        return struct.pack('>IBIII',
                           self.total_length,
                           self.id,
                           self.index,
                           self.begin,
                           self.length)

    @staticmethod
    def from_bytes(payload):
        _, _, index, begin, length = struct.unpack('>IBIII', payload)
        return Request(index, begin, length)


class BitField(Message):
    def __init__(self, bitfield):
        self.bitfield = BitArray(bitfield)

    @staticmethod
    def from_bytes(payload):
        # payload is the bitstring
        bitfield = BitArray(payload)
        return BitField(bitfield)

    # TODO: add to_bytes
    def to_bytes(self) -> bytes:
        raise NotImplemented


class Handshake(Message):
    def __init__(self, peer_id: bytes, info_hash: bytes, protocol: str = 'BitTorrent protocol'):
        self.id = MessageCode.HANDSHAKE
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


class Piece(Message):
    pass


class UnknownMessage(Message):
    def __init__(self, _id):
        self.id = _id

    def to_bytes(self) -> bytes:
        pass

    @staticmethod
    def from_bytes(payload):
        pass


class KeepAlive(Message):
    def to_bytes(self) -> bytes:
        pass

    @staticmethod
    def from_bytes(payload):
        pass
