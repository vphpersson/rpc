from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Type, Any
from abc import ABC, abstractmethod
from struct import unpack as struct_unpack, pack as struct_pack

from rpc.structures.pdu_type import PDUType
from rpc.structures.pfc_flag import PfcFlag
from rpc.structures.data_representation_format import DataRepresentationFormat, CharacterRepresentation, \
    IntegerRepresentation, FloatingPointRepresentation


@dataclass
class MSRPCHeader(ABC):
    pdu_type: ClassVar[PDUType] = NotImplemented
    pdu_type_to_class: ClassVar[dict[PDUType, Type[MSRPCHeader]]] = {}
    structure_size: ClassVar[int] = 16

    rpc_vers: int = 5
    rpc_vers_minor: int = 0
    pfc_flags: PfcFlag = PfcFlag.PFC_FIRST_FRAG | PfcFlag.PFC_LAST_FRAG
    packed_drep: DataRepresentationFormat = DataRepresentationFormat(
        character_representation=CharacterRepresentation.ASCII,
        integer_representation=IntegerRepresentation.LITTLE_ENDIAN,
        floating_point_representation=FloatingPointRepresentation.IEEE
    )
    call_id: int = 0

    @staticmethod
    def _from_bytes(data: bytes) -> dict[str, int | PDUType | PfcFlag | DataRepresentationFormat]:
        return dict(
            rpc_vers=data[0],
            rpc_vers_minor=data[1],
            pdu_type=PDUType(data[2]),
            pfc_flags=PfcFlag(data[3]),
            packed_drep=DataRepresentationFormat.from_bytes(data=data[4:8]),
            frag_length=struct_unpack('<H', data[8:10])[0],
            auth_length=struct_unpack('<H', data[10:12])[0],
            call_id=struct_unpack('<I', data[12:16])[0]
        )

    @property
    @abstractmethod
    def frag_length(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def auth_length(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def __bytes__(self) -> bytes:
        return b''.join([
            struct_pack('<B', self.rpc_vers),
            struct_pack('<B', self.rpc_vers_minor),
            struct_pack('<B', self.pdu_type),
            struct_pack('<B', self.pfc_flags.value),
            bytes(self.packed_drep),
            struct_pack('<H', self.frag_length),
            struct_pack('<H', self.auth_length),
            struct_pack('<I', self.call_id)
        ])

    @abstractmethod
    def _from_bytes_and_parameters(self, data: bytes, base_parameters: dict[str, Any]):
        raise NotImplementedError

    # TODO: Use dict method to find proper subtype.

    @classmethod
    def from_bytes(cls, data: bytes) -> MSRPCHeader:

        from rpc.pdu_headers.bind import BindHeader
        from rpc.pdu_headers.bind_ack import BindAckHeader
        from rpc.pdu_headers.request_header import RequestHeader
        from rpc.pdu_headers.response_header import ResponseHeader

        base_parameters: dict[str, int | PDUType | PfcFlag, DataRepresentationFormat] = cls._from_bytes(
            data=data
        )
        pdu_type = base_parameters.pop('pdu_type')

        if cls != MSRPCHeader:
            if pdu_type != cls.pdu_type:
                # TODO: Use proper exception.
                raise ValueError
            return cls._from_bytes_and_parameters(data=data, base_parameters=base_parameters)
        else:
            return cls.pdu_type_to_class[pdu_type]._from_bytes_and_parameters(
                data=data,
                base_parameters=base_parameters
            )


def register_pdu_header(cls: Type[MSRPCHeader]):
    cls.pdu_type_to_class[cls.pdu_type] = cls
    return cls
