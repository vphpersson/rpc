from __future__ import annotations
from typing import Final, Iterable, List
from struct import pack as struct_pack, unpack as struct_unpack


# TODO: Should this be a `tuple`?
class ContextList(list):
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
            b''.join(bytes(context_element) for context_element in self.__iter__())
        ])

    def byte_len(self) -> int:
        return self.structure_size + sum(len(context_element) for context_element in self.__iter__())

    @classmethod
    def from_bytes(cls, data: bytes) -> ContextList:
        n_context_elem: int = struct_unpack('<B', data[:1])[0]

        context_elements: List[ContextElement] = []
        offset = 4
        for i in range(n_context_elem):
            context_element = ContextElement.from_bytes(data[offset:])
            context_elements.append(context_element)
            offset += len(context_element)

        return cls(context_elements)