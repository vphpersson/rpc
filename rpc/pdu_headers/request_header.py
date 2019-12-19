from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Optional, Dict, Any
from uuid import UUID
from struct import unpack as struct_unpack, pack as struct_pack

from rpc.pdu_headers.base import MSRPCHeader
from rpc.structures.pdu_type import PDUType
from rpc.structures.auth_verifier import AuthVerifier
from rpc.structures.pfc_flag import PfcFlag


@dataclass
class RequestHeader(MSRPCHeader):
    pdu_type: ClassVar[PDUType] = PDUType.REQUEST
    structure_size: ClassVar[int] = MSRPCHeader.structure_size + 8

    alloc_hint: int = 0
    context_id: int = 0
    opnum: int = 0
    object_uuid: Optional[UUID] = None
    stub_data: bytes = b''
    auth_verifier: Optional[AuthVerifier] = None

    @property
    def frag_length(self) -> int:
        return sum([
            self.structure_size,
            len(self.object_uuid.bytes_le) if self.object_uuid is not None else 0,
            len(self.stub_data),
            len(self.auth_verifier) if self.auth_verifier is not None else 0
        ])

    @property
    def auth_length(self) -> int:
        return len(self.auth_verifier) if self.auth_verifier is not None else 0

    @classmethod
    def _from_bytes_and_parameters(cls, data: bytes, base_parameters: Dict[str, Any]) -> RequestHeader:

        header_specific_data = data[MSRPCHeader.structure_size:]

        frag_length = base_parameters.pop('frag_length')
        auth_length = base_parameters.pop('auth_length')

        if PfcFlag.PFC_OBJECT_UUID in base_parameters['pfc_flags']:
            object_uuid = UUID(bytes_le=header_specific_data[8:24])
            stub_data = header_specific_data[24:(-auth_length or None)]
        else:
            object_uuid = None
            stub_data = header_specific_data[8:(-auth_length or None)]

        return cls(
            **base_parameters,
            alloc_hint=struct_unpack('<I', header_specific_data[:4])[0],
            context_id=struct_unpack('<H', header_specific_data[4:6])[0],
            opnum=struct_unpack('<H', header_specific_data[6:8])[0],
            object_uuid=object_uuid,
            stub_data=stub_data,
            auth_verifier=(
                AuthVerifier.from_bytes(data=header_specific_data[-auth_length:])
                if auth_length != 0 else None
            )
        )

    def __bytes__(self) -> bytes:
        return super().__bytes__() + b''.join([
            struct_pack('<I', self.alloc_hint),
            struct_pack('<H', self.context_id),
            struct_pack('<H', self.opnum),
            self.object_uuid.bytes_le if self.object_uuid is not None else b'',
            self.stub_data,
            bytes(self.auth_verifier) if self.auth_verifier is not None else b''
        ])
