from typing import Any
from enum import Enum


class Kind(Enum):
    NULL = 0
    INTEGER = 1
    DOUBLE = 2
    SIMPLE_STRING = 3
    BULK_STRING = 4
    SIMPLE_ERROR = 5
    # BOOLEAN = 7
    # HASHTABLE = 8
    # LIST = 9


class Value:
    value: Any
    kind: Kind

    def __init__(self, value: Any, kind: Kind):
        self.kind = kind
        self.value = value

    def to_raw(self) -> str:
        match self.value:
            case Kind.NULL:
                return "+null\r\n"

            case Kind.INTEGER:
                return f":{self.value}\r\n"

            case Kind.DOUBLE:
                return f",{self.value}\r\n"

            case Kind.SIMPLE_STRING:
                return f"+{self.value}\r\n"

            case Kind.BULK_STRING:
                return f"${len(self.value)}\r\n{self.value}\r\n"

            case Kind.SIMPLE_ERROR:
                return f"-{self.value}\r\n"

            case _:
                return ""
