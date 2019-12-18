from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID
from struct import  pack as struct_pack, unpack as struct_unpack


@dataclass
class PresentationSyntax:
    struture_size: ClassVar[int] = 20

    if_uuid: UUID
    if_version: int

    def __bytes__(self) -> bytes:
        return b''.join([self.if_uuid.bytes_le, struct_pack('<I', self.if_version)])

    def __len__(self) -> int:
        return self.struture_size

    @classmethod
    def from_bytes(cls, data: bytes) -> PresentationSyntax:
        return cls(
            if_uuid=UUID(bytes_le=data[:16]),
            if_version=struct_unpack('<I', data[16:20])[0]
        )