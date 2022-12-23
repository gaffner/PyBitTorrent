import ipaddress
import logging
import socket
import struct

from bitstring import BitArray

from PyBitTorrent.Exceptions import PeerConnectionFailed, PeerDisconnected, PeerHandshakeFailed
from PyBitTorrent.Message import Message, Handshake, BitField, HaveMessage
from PyBitTorrent.MessageFactory import MessageFactory

HANDSHAKE_STRIPPED_SIZE = 48


class Peer:
    def __init__(self, ip: str, port: int, _id: str = '00000000000000000000'):
        self.ip = ip
        self.port = port
        self.id = _id
        self.connected = False  # only after handshake this will be true
        self.handshake = None  # Handshake still have not happened
        self.is_choked = True  # By default the client is choked
        self.bitfield: BitArray = BitArray()

        if type(ipaddress.ip_address(ip)) is ipaddress.IPv6Address:
            self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.settimeout(5)

    def __str__(self):
        return f'{self.ip}, {self.port}'  # Should add id

    def connect(self):
        """
        Connect to the target client
        """
        try:
            test_sock = socket.socket(self.socket.family, self.socket.type)
            test_sock.settimeout(2)
            test_sock.connect((self.ip, self.port))

            self.socket.connect((self.ip, self.port))

        except socket.error as e:
            raise PeerConnectionFailed(f"Failed to connect: {str(e)}")

    def do_handshake(self, my_id, info_hash):
        """
        Do handshake with fellow peer
        """
        self.handshake = Handshake(my_id, info_hash)
        handshake_bytes = self.handshake.to_bytes()

        self.socket.send(handshake_bytes)

        response = self.receive_message()
        self.verify_handshake(response)

    def verify_handshake(self, handshake):
        if self.handshake == handshake:
            self.connected = True
        else:
            raise PeerHandshakeFailed

    def set_bitfield(self, bitfield: BitField):
        self.bitfield = bitfield.bitfield

    def set_have(self, have: HaveMessage):
        if have.index < self.bitfield.length:
            self.bitfield[have.index] = True
        else:
            logging.getLogger('BitTorrent').critical(f'Have message {have.index} smaller then {self.bitfield.length}')

    def receive_message(self) -> Message:
        # After handshake
        # myid = random.randint(0, 65536)
        try:
            # print(f"{myid} Waiting for {self}")
            packet_length = self.socket.recv(1)

        except OSError:
            raise PeerDisconnected

        if packet_length == b'':
            # logging.getLogger('BitTorrent').debug(f'Client in ip {self.ip} with id {self.id} disconnected')
            self.socket.close()
            # print(f"{myid}done")
            raise PeerDisconnected

        if self.connected:
            packet_length = packet_length + self.socket.recv(3)
            while len(packet_length) < 4:
                odd = 4 - len(packet_length)
                packet_length = packet_length + self.socket.recv(odd)
                logging.getLogger('BitTorrent').error(f"Setting size again in {self}, length: {packet_length}")
                # print('.')

            try:
                length = struct.unpack('>I', packet_length)[0]  # Big endian integer
            except struct.error:
                # print(f"{myid}The packet length:", packet_length)
                raise struct.error
            data = self.socket.recv(length)

            while len(data) != length:
                odd = length - len(data)
                data += self.socket.recv(odd)
                # print('.')

            #             # print(f"{myid}done")
            return MessageFactory.create_message(data)

        else:
            protocol_len: int = struct.unpack('>B', packet_length)[0]
            handshake_bytes = self.socket.recv(protocol_len + HANDSHAKE_STRIPPED_SIZE)

            # print(f"{myid}done")
            return MessageFactory.create_handshake_message(packet_length + handshake_bytes)

    def send_message(self, message: Message):
        # logging.getLogger('BitTorrent').debug(f'Sending message {type(message)} to {self}')
        if not self.connected:
            pass
        message_bytes = message.to_bytes()
        try:
            self.socket.send(message_bytes)
        except OSError:
            raise PeerDisconnected

    def set_choked(self):
        self.is_choked = True

    def set_unchoked(self):
        self.is_choked = False

    def have_piece(self, piece):
        if piece.index < self.bitfield.length:
            return self.bitfield[piece.index]
        else:
            return False
