from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar
from struct import pack as struct_pack


class CharacterRepresentation(IntEnum):
    ASCII = 0
    EBCDIC = 1


class IntegerRepresentation(IntEnum):
    BIG_ENDIAN = 0
    LITTLE_ENDIAN = 1


class FloatingPointRepresentation(IntEnum):
    IEEE = 0
    VAX = 1
    CRAY = 2
    IBM = 3


@dataclass
class DataRepresentationFormat:
    _reserved: ClassVar[bytes] = bytes(2)

    character_representation: CharacterRepresentation
    integer_representation: IntegerRepresentation
    floating_point_representation: FloatingPointRepresentation

    @classmethod
    def from_bytes(cls, data: bytes) -> DataRepresentationFormat:

        if data[2:4] != cls._reserved:
            # TODO: Use proper exception.
            raise ValueError

        return cls(
            character_representation=CharacterRepresentation(data[0] & 0b1111),
            integer_representation=IntegerRepresentation((data[0] >> 4) & 0b1111),
            floating_point_representation=FloatingPointRepresentation(data[1])
        )

    def __bytes__(self) -> bytes:
        return b''.join([
            struct_pack('<B', (self.integer_representation.value << 4) | self.character_representation.value),
            struct_pack('<B', self.floating_point_representation.value),
            self._reserved
        ])
