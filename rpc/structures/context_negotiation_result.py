from dataclasses import dataclass


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