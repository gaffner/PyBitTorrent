import socket


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
        self.socket.connect((self.ip, self.port))
