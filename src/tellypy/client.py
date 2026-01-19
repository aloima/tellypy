from .kinds import Value, Kind
from enum import Enum
import socket


class Protocol(Enum):
    RESP2 = 2
    RESP3 = 3


class Client:
    connected: bool
    socket: socket.client
    protocol: Protocol

    def __init__(self):
        self.connected = False

    def connect(self, host: str, port: int, proto: Protocol = Protocol.RESP2):
        self.protocol = proto
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

    def execute_command(self, command: str):
        data = [Value(data, Kind.BULK_STRING) for data in command.split()]
        self.client.send(Value(data, Kind.ARRAY).to_raw())
        res = self.client.recv(1024)

        return res
