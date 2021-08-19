from typing import ByteString, get_args, Any, Type, Deque, SupportsInt
from logging import getLogger
from collections import deque
from struct import pack
from inspect import isclass

from ndr.structures import NDRType
from ndr.structures.pointer import Pointer, NullPointer
from ndr.utils import calculate_pad_length, pad as ndr_pad

from rpc.utils.types import DWORD, LPDWORD, LPBYTE, LPBYTE_VAR, CTYPE_TO_STRUCT

LOG = getLogger(__name__)


def unpack_structure(data: ByteString, structure: dict[str, tuple[Type, ...]], offset: int = 0) -> dict[str, Any]:

    data = memoryview(data)[offset:]
    offset = 0

    structure_values: dict[str, Any] = {}

    for value_name, item_types in structure.items():
        item_data = data[offset:]

        item_types_deque: Deque[Type] = deque(item_types)

        while True:
            try:
                item_type = item_types_deque.popleft()
            except IndexError:
                break

            if item_type in {LPDWORD, LPBYTE, LPBYTE_VAR}:
                item_types_deque.extendleft(reversed(get_args(item_type)))
            elif item_type in {DWORD}:
                struct = CTYPE_TO_STRUCT[item_type.__supertype__]

                item_data = struct.unpack_from(buffer=item_data)[0]
                offset += struct.size
            elif item_type is Pointer:
                pointer = Pointer.from_bytes(data=item_data)
                item_data = pointer.representation
                offset += Pointer.structure_size
            else:
                if isinstance(item_data, (ByteString, memoryview)):
                    item_data = item_type.from_bytes(item_data)

                    if issubclass(item_type, NDRType):
                        offset += calculate_pad_length(length_unpadded=len(item_data))
                    else:
                        offset += len(item_data)

                    if hasattr(item_data, 'representation'):
                        item_data = item_data.representation
                else:
                    item_data = item_type(item_data)

        structure_values[value_name] = item_data

    return structure_values


def pack_structure(instance, structure: dict[str, tuple[Type, ...]]) -> bytes:

    structure_bytes: dict[str, bytes] = {}

    for value_name, item_types in structure.items():

        item_types_deque: Deque[Type] = deque(item_types)

        value_name = value_name.removeprefix('__') if value_name.startswith('__') else value_name

        item_data = getattr(instance, value_name)

        while True:
            try:
                item_type = item_types_deque.pop()
            except IndexError:
                break

            if isinstance(item_data, NDRType):
                item_data = ndr_pad(bytes(item_data))
            elif isclass(item_type) and issubclass(item_type, NullPointer):
                item_data = bytes(4)
            elif isclass(item_type) and issubclass(item_type, NDRType):
                item_data = ndr_pad(bytes(item_type(representation=item_data)))
            elif item_type in {DWORD}:
                item_data = pack('<I', int(item_data))
            elif item_type in {LPDWORD, LPBYTE, LPBYTE_VAR}:
                item_types_deque.extendleft(reversed(get_args(item_type)))
            elif isinstance(item_type, SupportsInt):
                item_data = int(item_data)
            else:
                LOG.info(f'Item type {item_type} skipped for instance {instance}.')

        structure_bytes[value_name] = item_data

    return b''.join(list(structure_bytes.values()))

