from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Tuple, List
from struct import pack as struct_pack, unpack as struct_unpack

from rpc.structures.presentation_syntax import PresentationSyntax


@dataclass
class ContextElement:
    structure_size: ClassVar[int] = 24
    _reserved: ClassVar[bytes] = bytes(1)

    context_id: int
    abstract_syntax: PresentationSyntax
    transfer_syntaxes: Tuple[PresentationSyntax, ...]

    @property
    def n_transfer_syn(self) -> int:
        return len(self.transfer_syntaxes)

    def __bytes__(self) -> bytes:
        return b''.join([
            struct_pack('<H', self.context_id),
            struct_pack('<B', self.n_transfer_syn),
            self._reserved,
            bytes(self.abstract_syntax),
            b''.join(bytes(transfer_syntax) for transfer_syntax in self.transfer_syntaxes)
        ])

    def __len__(self) -> int:
        return self.structure_size + self.n_transfer_syn * PresentationSyntax.struture_size

    @classmethod
    def from_bytes(cls, data: bytes) -> ContextElement:
        n_transfer_syntax: int = struct_unpack('<B', data[2:3])[0]
        transfer_syntaxes: List[PresentationSyntax] = []
        offset = 24
        for i in range(n_transfer_syntax):
            transfer_syntaxes.append(PresentationSyntax.from_bytes(data[offset:offset+20]))
            offset += PresentationSyntax.struture_size

        return cls(
            context_id=struct_unpack('<H', data[0:2])[0],
            abstract_syntax=PresentationSyntax.from_bytes(data=data[4:24]),
            transfer_syntaxes=tuple(transfer_syntaxes)
        )
