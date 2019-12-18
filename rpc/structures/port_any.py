from __future__ import annotations
from dataclasses import dataclass
from struct import pack as struct_pack, unpack as struct_unpack


@dataclass
class PortAny:
    port_spec: str

    def __bytes__(self) -> bytes:
        # TODO: Verify that this serialization is correct.
        return b''.join([
            struct_pack('<H', len(self.port_spec) + 1),
            self.port_spec.encode(encoding='ascii') + b'\x00'
        ])

    def __len__(self) -> int:
        return len(self.__bytes__())

    @classmethod
    def from_bytes(cls, data: bytes) -> PortAny:
        length: int = struct_unpack('<H', data[:2])[0]
        return cls(port_spec=data[2:2+length-1].decode(encoding='ascii'))