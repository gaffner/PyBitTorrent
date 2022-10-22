import socket
import struct

from Exceptions import PeerConnectionFailed
from Message import Message
from MessageFactory import MessageFactory


class Peer:
    def __init__(self, ip: str, port: int, _id: str):
        self.ip = ip
        self.port = port
        self.id = _id
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

    def handshake(self):
        pass

    def receive_message(self) -> Message:
        length = struct.unpack('<I', self.socket.recv(1))  # Big endian integer
        data = self.socket.recv(length)

        return MessageFactory.create_message(data)
