from typing import Any
from enum import Enum


class Kind(Enum):
    NULL = 0
    INTEGER = 1
    DOUBLE = 2
    SIMPLE_STRING = 3
    BULK_STRING = 4
    SIMPLE_ERROR = 5
    ARRAY = 6
    # BOOLEAN = 7
    # HASHTABLE = 8
    # LIST = 9


class Value:
    data: Any
    kind: Kind

    def __init__(self, data: Any, kind: Kind):
        self.kind = kind
        self.data = data

    def to_raw(self) -> str:
        match self.kind:
            case Kind.NULL:
                return "+null\r\n"

            case Kind.INTEGER:
                return f":{self.data}\r\n"

            case Kind.DOUBLE:
                return f",{self.data}\r\n"

            case Kind.SIMPLE_STRING:
                return f"+{self.data}\r\n"

            case Kind.BULK_STRING:
                return f"${len(self.data)}\r\n{self.data}\r\n"

            case Kind.SIMPLE_ERROR:
                return f"-{self.data}\r\n"

            case Kind.ARRAY:
                length = len(self.data)
                data = [value.to_raw() for value in self.data]
                return f"*{length}\r\n{"".join(data)}"

            case _:
                return ""
