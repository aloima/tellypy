from typing import Any
from enum import Enum

r_a = ord("\r")
n_a = ord("\n")


class Kind(Enum):
    NULL = ord("_")
    INTEGER = ord(":")
    DOUBLE = ord(",")
    SIMPLE_STRING = ord("+")
    BULK_STRING = ord("$")
    SIMPLE_ERROR = ord("-")
    ARRAY = ord("*")
    # BOOLEAN = 7
    # HASHTABLE = 8
    # LIST = 9


class Value:
    data: Any
    kind: Kind

    def __init__(self, data: Any, kind: Kind):
        self.kind = kind
        self.data = data

    @staticmethod
    def from_raw(value: memoryview) -> tuple["Value", int]:
        match value[0]:
            case Kind.NULL.value:
                return Value(None, Kind.NULL)

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
                    n = idx + 2

                    return Value(data.decode("utf-8"), Kind.SIMPLE_STRING), n

            case Kind.BULK_STRING.value:
                start = value.index(r_a)
                length = int(value[1:start])

                data = value[(start + 2):(start + length)].tobytes()
                n = start + length + 4

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
                        subvalue, parsed = Value.from_raw(value[total:])
                        data.append(subvalue)
                        total += parsed

                    return Value(data, Kind.SIMPLE_ERROR), total

        return Value(None, Kind.NULL), 0

    def to_raw(self) -> str:
        match self.kind:
            case Kind.NULL:
                return bytes("+null\r\n", "utf-8")

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
                data = [value.to_raw().decode("utf-8") for value in self.data]
                return bytes(f"*{length}\r\n{"".join(data)}", "utf-8")

            case _:
                return ""
