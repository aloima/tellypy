from importlib.metadata import version
from enum import Enum
import socket

from .kinds import Value, Kind


class Protocol(Enum):
    RESP2 = 2
    RESP3 = 3


class Client:
    __id: int = -1
    __preconnected: bool = False
    __connected: bool = False
    __socket: socket.client = None
    __protocol: Protocol = None

    __host: str
    __port: int

    def __init__(self, host: str, port: int = 6379):
        self.__host = host
        self.__port = port

    def connect(self, set_info: bool = True,
                protocol: Protocol = Protocol.RESP2) -> bool:
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.connect((self.__host, self.__port))
            self.__preconnected = True

            self.__id = self.execute_command("CLIENT ID").data
            self.execute_command(f"HELLO {protocol.value}")

            if set_info:
                lib_name = __package__.split(".")[0]
                lib_ver = version(lib_name)
                self.execute_command(f"CLIENT SETINFO LIB-NAME {lib_name}")
                self.execute_command(f"CLIENT SETINFO LIB-VERSION {lib_ver}")

        except Exception as error:
            self.__connected = False
            raise error

        else:
            self.__connected = True
            return True

    def is_connected(self) -> bool:
        return self.__connected

    def get_id(self) -> int:
        return self.__id

    def execute_command(self, command: str) -> Value:
        if not self.__preconnected:
            return

        data = [Value(data, Kind.BULK_STRING) for data in command.split()]
        self.__socket.send(Value(data, Kind.ARRAY).to_raw())
        res = self.__socket.recv(1024)

        return Value.from_raw(memoryview(res))[0]
