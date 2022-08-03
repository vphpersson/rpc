from __future__ import annotations
from typing import Final, Iterable
from struct import unpack as struct_unpack, pack as struct_pack

from rpc.structures.context_negotiation_result import ContextNegotiationResult


class ResultList(list):
    structure_size: Final[int] = 4
    _reserved: bytes = bytes(1)
    _reserved2: bytes = bytes(2)

    def __init__(self, sequence: Iterable = ()):
        super().__init__(sequence)

    def __bytes__(self) -> bytes:
        return b''.join([
            struct_pack('<B', self.__len__()),
            self._reserved,
            self._reserved2,
            b''.join(bytes(result) for result in self.__iter__())
        ])

    def byte_len(self) -> int:
        return self.structure_size + sum(len(result) for result in self.__iter__())

    @classmethod
    def from_bytes(cls, data: bytes) -> ResultList:
        n_results: int = struct_unpack('<B', data[:1])[0]

        results: list[ContextNegotiationResult] = []
        offset = 4
        for i in range(n_results):
            result = ContextNegotiationResult.from_bytes(data=data[offset:])
            results.append(result)
            offset += len(result)

        return cls(sequence=results)
