import ipaddress
import logging
import socket
import struct

from bitstring import BitArray

from Exceptions import PeerConnectionFailed, PeerDisconnected
from Message import Message, Handshake, BitField, HaveMessage
from MessageFactory import MessageFactory

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
            # self.socket.settimeout()
            # self.socket.gettimeout()
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

    def verify_handshake(self, handshake) -> bool:
        if self.handshake == handshake:
            self.connected = True
            return True

        return False

    def set_bitfield(self, bitfield: BitField):
        self.bitfield = bitfield.bitfield

    def set_have(self, have: HaveMessage):
        if have.index < self.bitfield.length:
            self.bitfield[have.index] = True
        else:
            logging.getLogger('BitTorrent').critical(f'Have message {have.index} smaller then {self.bitfield.length}')

    def receive_message(self) -> Message:
        # After handshake
        try:
            packet_length = self.socket.recv(1)
        except WindowsError:
            raise PeerDisconnected

        if packet_length == b'':
            logging.getLogger('BitTorrent').error(f'Client in ip {self.ip} with id {self.id} disconnected')
            self.socket.close()
            raise PeerDisconnected

        if self.connected:
            packet_length = packet_length + self.socket.recv(3)
            length = struct.unpack('>I', packet_length)[0]  # Big endian integer
            data = self.socket.recv(length)

            while len(data) != length:
                odd = length - len(data)
                data += self.socket.recv(odd)

            logging.getLogger('BitTorrent').debug(f"packet length: {length}")
            return MessageFactory.create_message(data)
            # message = MessageFactory.create_message(data)
            # if message.should_wait_for_data():
            #     print("Waiting for data...")


        # Before handshake
        else:
            logging.getLogger('BitTorrent').debug(
                f'Receiving handshake response from {self.id} with length {packet_length}')
            protocol_len: int = struct.unpack('>B', packet_length)[0]
            handshake_bytes = self.socket.recv(protocol_len + HANDSHAKE_STRIPPED_SIZE)

            return MessageFactory.create_handshake_message(packet_length + handshake_bytes)

    def send_message(self, message: Message):
        # logging.getLogger('BitTorrent').debug(f'Sending message {type(message)} to {self}')
        message_bytes = message.to_bytes()
        try:
            self.socket.send(message_bytes)
        except OSError:
            raise PeerDisconnected

    def set_unchoke(self, _):
        self.is_choked = False

    def have_piece(self, piece):
        if piece.index < self.bitfield.length:
            return self.bitfield[piece.index]
        else:
            return False
