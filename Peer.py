import logging
import socket
import struct

from Exceptions import PeerConnectionFailed
from Message import Message, Handshake
from MessageFactory import MessageFactory

HANDSHAKE_STRIPPED_SIZE = 48


class Peer:
    def __init__(self, ip: str, port: int, _id: str = None):
        self.ip = ip
        self.port = port
        self.id = _id
        self.connected = False  # only after handshake this will be true
        self.handshake = None
        self.socket: socket.socket = socket.socket()

    def __str__(self):
        return f'Client {self.ip}:{self.port}:{self.id[:5]}'

    def connect(self):
        """
        Connect to the target client
        """
        try:
            self.socket.connect((self.ip, self.port))
        except socket.error:
            raise PeerConnectionFailed("Failed to connect")

    def handshake(self, my_id, info_hash):
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

    def receive_message(self) -> Message:
        # After handshake
        if self.connected:
            length = struct.unpack('>', self.socket.recv(4))[0]  # Big endian integer
            data = self.socket.recv(length)
            return MessageFactory.create_message(data)

        # Before handshake
        else:
            logging.getLogger('BitTorrent').info(f'Receiving handshake response from {self.id}')
            protocol_len_bytes = self.socket.recv(1)
            protocol_len: int = struct.unpack('>B', protocol_len_bytes)[0]
            handshake_bytes = self.socket.recv(protocol_len + HANDSHAKE_STRIPPED_SIZE)

            return MessageFactory.create_handshake_message(protocol_len_bytes + handshake_bytes)
