from dataclasses import dataclass, field
from typing import ClassVar, Optional, Dict, Any
from struct import pack as struct_pack, unpack as struct_unpack

from rpc.pdu_headers.base import MSRPCHeader
from rpc.structures.pdu_type import PDUType
from rpc.structures.port_any import PortAny
from rpc.structures.result_list import ResultList
from rpc.structures.auth_verifier import AuthVerifier


@dataclass
class BindAckHeader(MSRPCHeader):
    pdu_type: ClassVar[PDUType] = PDUType.BIND_ACK
    structure_size: ClassVar[int] = MSRPCHeader.structure_size + 8

    max_xmit_frag: int = 4280
    max_recv_frag: int = 4280
    assoc_group_id: int = 0
    result_list: ResultList = field(default_factory=ResultList())
    sec_addr: Optional[PortAny] = None
    auth_verifier: Optional[AuthVerifier] = None

    @property
    def frag_length(self) -> int:

        if self.sec_addr is not None:
            sec_addr_len = len(self.sec_addr)
            num_padding = (4 - (sec_addr_len % 4)) % 4
        else:
            sec_addr_len = 0
            num_padding = 0

        return sum([
            self.structure_size,
            sec_addr_len,
            num_padding,
            self.result_list.byte_len(),
            self.auth_length
        ])

    @property
    def auth_length(self) -> int:
        return len(self.auth_verifier) if self.auth_verifier is not None else 0

    @classmethod
    def _from_bytes_and_parameters(cls, data: bytes, base_parameters: Dict[str, Any]):

        header_specific_data = data[MSRPCHeader.structure_size:]

        frag_length = base_parameters.pop('frag_length')
        auth_length = base_parameters.pop('auth_length')

        # TODO: Not sure how to deal with the fact that this is optional.
        sec_addr = PortAny.from_bytes(data=header_specific_data[8:])

        num_padding = (4 - (len(sec_addr) % 4)) % 4
        result_list_offset = 8 + len(sec_addr) + num_padding
        result_list = ResultList.from_bytes(data=header_specific_data[result_list_offset:])

        # TODO: Support `auth_verifier`.

        return cls(
            **base_parameters,
            max_xmit_frag=struct_unpack('<H', header_specific_data[:2])[0],
            max_recv_frag=struct_unpack('<H', header_specific_data[2:4])[0],
            assoc_group_id=struct_unpack('<I', header_specific_data[4:8])[0],
            sec_addr=sec_addr,
            result_list=result_list
        )

    def __bytes__(self) -> bytes:

        # TODO: Deal with the optional case somehow.
        num_padding = (4 - (len(self.sec_addr) % 4)) % 4
        # TODO: Deal with the `auth_verifier` case.

        return super().__bytes__() + b''.join([
            struct_pack('<H', self.max_xmit_frag),
            struct_pack('<H', self.max_recv_frag),
            struct_pack('<I', self.assoc_group_id),
            bytes(self.sec_addr),
            num_padding * b'\x00',
            bytes(self.result_list)
        ])
