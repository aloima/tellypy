from typing import Any
from enum import Enum

from .protocols import Protocol

r_a = ord("\r")
n_a = ord("\n")
t_a = ord("t")
f_a = ord("f")


class Kind(Enum):
    NULL = ord("_")
    INTEGER = ord(":")
    DOUBLE = ord(",")
    SIMPLE_STRING = ord("+")
    BULK_STRING = ord("$")
    SIMPLE_ERROR = ord("-")
    ARRAY = ord("*")
    BOOLEAN = ord("#")
    # HASHTABLE = 8
    # LIST = 9


class Value:
    data: Any
    kind: Kind

    def __init__(self, data: Any, kind: Kind):
        self.kind = kind
        self.data = data

    @staticmethod
    def from_raw(protocol: Protocol, value: memoryview) -> tuple["Value", int]:
        match value[0]:
            case Kind.NULL.value:
                return Value(None, Kind.NULL), 3

            case Kind.INTEGER.value:
                idx = value.index(r_a)

                if idx != -1 and value[idx + 1] == n_a:
                    data = value[1:idx]
                    n = idx + 2

                    return Value(int(data), Kind.INTEGER), n

            case Kind.DOUBLE.value:
                idx = value.index(r_a)

                if idx != -1 and value[idx + 1] == n_a:
                    data = value[1:idx]
                    n = idx + 2

                    return Value(float(data), Kind.DOUBLE), n

            case Kind.SIMPLE_STRING.value:
                idx = value.index(r_a)

                if idx != -1 and value[idx + 1] == n_a:
                    data = value[1:idx].tobytes()
                    res = data.decode("utf-8")
                    n = idx + 2

                    if protocol == Protocol.RESP2:
                        match res:
                            case "true":
                                return Value(True, Kind.BOOLEAN), n

                            case "false":
                                return Value(False, Kind.BOOLEAN), n

                            case _:
                                return Value(res, Kind.SIMPLE_STRING), n

                    return Value(res, Kind.SIMPLE_STRING), n

            case Kind.BULK_STRING.value:
                start = value.index(r_a)
                length = int(value[1:start])
                start += 2  # pass \r\n

                if length == -1 and protocol == Protocol.RESP2:
                    return Value(None, Kind.NULL), start

                data = value[start:(start + length)].tobytes()
                n = start + length + 2

                return Value(data.decode("utf-8"), Kind.BULK_STRING), n

            case Kind.SIMPLE_ERROR.value:
                idx = value.index(r_a)

                if idx != -1:
                    data = value[1:idx].tobytes()
                    n = idx + 2

                    return Value(data.decode("utf-8"), Kind.SIMPLE_ERROR), n

            case Kind.ARRAY.value:
                idx = value.index(r_a)

                if idx != -1 and value[idx + 1] == n_a:
                    count = int(value[1:idx])
                    data: list[Value] = []
                    total = idx + 2

                    for _ in range(count):
                        subvalue, parsed = Value.from_raw(
                                                protocol, value[total:])
                        data.append(subvalue)
                        total += parsed

                    return Value(data, Kind.ARRAY), total

            case Kind.BOOLEAN.value:
                valid = (value[1] == t_a or value[1] == f_a)

                if protocol == Protocol.RESP3 and valid:
                    if value[2] == r_a and value[3] == n_a:
                        return Value(value[1] == t_a, Kind.BOOLEAN), 4

        return Value(None, Kind.NULL), 0

    def to_raw(self, protocol: Protocol) -> str:
        match self.kind:
            case Kind.NULL:
                match protocol:
                    case Protocol.RESP2:
                        return bytes("$-1\r\n", "utf-8")

                    case Protocol.RESP3:
                        return bytes("_\r\n", "utf-8")

            case Kind.INTEGER:
                return bytes(f":{self.data}\r\n", "utf-8")

            case Kind.DOUBLE:
                return bytes(f",{self.data}\r\n", "utf-8")

            case Kind.SIMPLE_STRING:
                return bytes(f"+{self.data}\r\n", "utf-8")

            case Kind.BULK_STRING:
                return bytes(f"${len(self.data)}\r\n{self.data}\r\n", "utf-8")

            case Kind.SIMPLE_ERROR:
                return bytes(f"-{self.data}\r\n", "utf-8")

            case Kind.ARRAY:
                length = len(self.data)
                data = [
                    value.to_raw(protocol).decode("utf-8")
                    for value in self.data
                ]

                return bytes(f"*{length}\r\n{"".join(data)}", "utf-8")

            case Kind.BOOLEAN:
                match protocol:
                    case Protocol.RESP2:
                        value = "true" if self.data else "false"
                        return bytes(f"+{value}\r\n", "utf-8")

                    case Protocol.RESP3:
                        value = "t" if self.data else "f"
                        return bytes(f"#{value}\r\n", "utf-8")

            case _:
                return ""
