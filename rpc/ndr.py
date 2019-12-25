from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional, Union, Iterator, Final, ClassVar
from struct import unpack as struct_unpack, pack as struct_pack
from uuid import UUID

from rpc.structures.presentation_syntax import PresentationSyntax


NDR_PRESENTATION_SYNTAX = PresentationSyntax(if_uuid=UUID('8a885d04-1ceb-11c9-9fe8-08002b104860'), if_version=2)


class NDRType(ABC):

    _referent_id_iterator: Final[Iterator[int]] = iter(range(1, 2**32 - 1))

    @abstractmethod
    def __bytes__(self) -> bytes:
        raise NotImplementedError


# TODO: The string encoding should be whatever the data representation format label says, no?
class ConformantVaryingString(NDRType):
    def __init__(self, representation: str = '', offset: int = 0, maximum_count: Optional[int] = None):
        self.representation: str = representation
        self.offset: int = offset
        self._maximum_count: Optional[int] = maximum_count

    @property
    def actual_count(self) -> int:
        # Length of string plus a null byte
        return len(self.representation) + 1

    @property
    def maximum_count(self) -> int:
        return self._maximum_count if self._maximum_count is not None else self.actual_count

    @maximum_count.setter
    def maximum_count(self, value: int):
        self._maximum_count = value

    @classmethod
    def from_bytes(cls, data: bytes) -> ConformantVaryingString:
        actual_count: int = struct_unpack('<I', data[8:12])[0]

        # TODO: I don't know why the elements are of size 2 -- figure out?
        return cls(
            representation=data[12:12+2*actual_count].decode(encoding='utf-16-le').rstrip('\x00'),
            offset=struct_unpack('<I', data[4:8])[0],
            maximum_count=struct_unpack('<I', data[:4])[0]
        )

    def __bytes__(self) -> bytes:
        return b''.join([
            struct_pack('<I', self.maximum_count),
            struct_pack('<I', self.offset),
            struct_pack('<I', self.actual_count),
            self.representation.encode(encoding='utf-16-le') + 2 * b'\x00'
        ])

    def __len__(self) -> int:
        return len(self.__bytes__())


@dataclass
class NDRUnion(NDRType):
    tag: int
    representation: Union[NDRType, bytes]

    @classmethod
    def from_bytes(cls, data: bytes) -> NDRUnion:
        return cls(tag=struct_unpack('<I', data[:4])[0], representation=data[4:])

    def __bytes__(self) -> bytes:
        return struct_pack('<I', self.tag) + bytes(self.representation)


@dataclass
class Pointer(NDRType):
    representation: Union[NDRType, bytes]
    referent_id: int = field(default_factory=lambda: next(NDRType._referent_id_iterator))
    structure_size: ClassVar[int] = 4

    @classmethod
    def from_bytes(cls, data: bytes) -> Pointer:
        return cls(
            referent_id=struct_unpack('<I', data[:4])[0],
            representation=data[4:]
        )

    def __bytes__(self) -> bytes:
        return struct_pack('<I', self.referent_id) + bytes(self.representation)
