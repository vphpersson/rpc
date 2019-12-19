from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Optional, Dict, Any
from struct import unpack as struct_unpack, pack as struct_pack

from rpc.pdu_headers.base import MSRPCHeader
from rpc.structures.pdu_type import PDUType
from rpc.structures.auth_verifier import AuthVerifier


@dataclass
class ResponseHeader(MSRPCHeader):
    pdu_type: ClassVar[PDUType] = PDUType.RESPONSE
    structure_size: ClassVar[int] = MSRPCHeader.structure_size + 8
    _reserved: ClassVar[bytes] = bytes(1)

    alloc_hint: int = 0
    context_id: int = 0
    cancel_count: int = 0
    stub_data: bytes = b''
    auth_verifier: Optional[AuthVerifier] = None

    @property
    def frag_length(self) -> int:
        return sum([
            self.structure_size,
            len(self.stub_data),
            len(self.auth_verifier) if self.auth_verifier is not None else 0
        ])

    @property
    def auth_length(self) -> int:
        return len(self.auth_verifier) if self.auth_verifier is not None else 0

    @classmethod
    def _from_bytes_and_parameters(cls, data: bytes, base_parameters: Dict[str, Any]) -> ResponseHeader:

        header_specific_data = data[MSRPCHeader.structure_size:]

        frag_length = base_parameters.pop('frag_length')
        auth_length = base_parameters.pop('auth_length')

        return cls(
            **base_parameters,
            alloc_hint=struct_unpack('<I', header_specific_data[:4])[0],
            context_id=struct_unpack('<H', header_specific_data[4:6])[0],
            cancel_count=struct_unpack('<B', header_specific_data[6:7])[0],
            stub_data=header_specific_data[8:(-auth_length or None)],
            auth_verifier=(
                AuthVerifier.from_bytes(data=header_specific_data[-auth_length:])
                if auth_length != 0 else None
            )
        )

    def __bytes__(self) -> bytes:
        return super().__bytes__() + b''.join([
            struct_pack('<I', self.alloc_hint),
            struct_pack('<H', self.context_id),
            struct_pack('<B', self.cancel_count),
            struct_pack('<B', self._reserved),
            self.stub_data,
            bytes(self.auth_verifier) if self.auth_verifier is not None else b''
        ])
