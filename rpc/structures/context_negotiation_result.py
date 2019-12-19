from __future__ import annotations
from dataclasses import dataclass
from struct import unpack as struct_unpack, pack as struct_pack
from enum import IntEnum
from typing import Optional

from rpc.structures.presentation_syntax import PresentationSyntax


class ContDefResult(IntEnum):
    ACCEPTANCE = 0
    USER_REJECTION = 1
    PROVIDER_REJECTION = 2


class ProviderReason(IntEnum):
    REASON_NOT_SPECIFIED = 0
    ABSTRACT_SYNTAX_NOT_SUPPORTED = 1
    PROPOSED_TRANSFER_SYNTAXES_NOT_SUPPORTED = 2
    LOCAL_LIMIT_EXCEEDED = 3


@dataclass
class ContextNegotiationResult:
    result: ContDefResult
    reason: ProviderReason
    transfer_syntax: Optional[PresentationSyntax]

    def __len__(self) -> int:
        return 4 + (self.transfer_syntax.struture_size if self.transfer_syntax is not None else 0)

    def __bytes__(self) -> bytes:
        return b''.join([
            struct_pack('<H', self.result.value),
            struct_pack('<H', self.reason.value),
            bytes(self.transfer_syntax) if self.transfer_syntax is not None else b''
        ])

    @classmethod
    def from_bytes(cls, data: bytes) -> ContextNegotiationResult:
        result = ContDefResult(struct_unpack('<H', data[:2])[0])

        return cls(
            result=result,
            reason=ProviderReason(struct_unpack('<H', data[2:4])[0]),
            transfer_syntax=(
                PresentationSyntax.from_bytes(data=data[4:24]) if result is ContDefResult.ACCEPTANCE
                else None
            )
        )
