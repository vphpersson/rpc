from typing import Annotated, NewType
from struct import Struct
from ctypes import c_ulong

from ndr.structures.pointer import Pointer
from ndr.structures.unidimensional_conformant_array import UnidimensionalConformantArray
from ndr.structures.unidimensional_conformant_varying_array import UnidimensionalConformantVaryingArray


CTYPE_TO_STRUCT = {
    c_ulong: Struct('<I')
}

DWORD = NewType('DWORD', c_ulong)
BYTE_ARRAY = UnidimensionalConformantArray
BYTE_ARRAY_VAR = UnidimensionalConformantVaryingArray
LPBYTE = Annotated[Pointer, BYTE_ARRAY]
LPBYTE_VAR = Annotated[Pointer, BYTE_ARRAY_VAR]
LPDWORD = Annotated[Pointer, DWORD]
