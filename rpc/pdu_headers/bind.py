from dataclasses import dataclass, field
from typing import Optional, ClassVar, Dict
from struct import unpack as struct_unpack, pack as struct_pack

from rpc.pdu_headers.base import MSRPCHeader
from rpc.structures.auth_verifier import AuthVerifier
from rpc.structures.context_list import ContextList
from rpc.structures.pdu_type import PDUType


@dataclass
class BindHeader(MSRPCHeader):
    pdu_type: ClassVar[PDUType] = PDUType.BIND
    structure_size: ClassVar[int] = MSRPCHeader.structure_size + 8

    presentation_context_list: ContextList = field(default_factory=ContextList)
    assoc_group_id: int = 0
    max_xmit_frag: int = 4280
    max_recv_frag: int = 4280
    auth_verifier: Optional[AuthVerifier] = None

    @property
    def frag_length(self) -> int:
        return sum([
            self.structure_size,
            self.presentation_context_list.byte_len(),
            self.auth_length
        ])

    @property
    def auth_length(self) -> int:
        return len(self.auth_verifier) if self.auth_verifier is not None else 0

    # TODO: Add type.
    @classmethod
    def _from_bytes_and_parameters(cls, data: bytes, base_parameters: Dict[str, ...]):

        header_specific_data = data[MSRPCHeader.structure_size:]

        frag_length = base_parameters.pop('frag_length')
        auth_length = base_parameters.pop('auth_length')

        return cls(
            **base_parameters,
            max_xmit_frag=struct_unpack('<H', header_specific_data[:2])[0],
            max_recv_frag=struct_unpack('<H', header_specific_data[2:4])[0],
            assoc_group_id=struct_unpack('<I', header_specific_data[4:8])[0],
            presentation_context_list=ContextList.from_bytes(header_specific_data[8:]),
            # auth_verifier=AuthVerifier
        )

    def __bytes__(self) -> bytes:
        return super().__bytes__() + b''.join([
            struct_pack('<H', self.max_xmit_frag),
            struct_pack('<H', self.max_recv_frag),
            struct_pack('<I', self.assoc_group_id),
            bytes(self.presentation_context_list)
        ])
