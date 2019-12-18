from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class AuthVerifier:
    _auth_reserved: ClassVar[bytes] = bytes(1)

    auth_level: int
    auth_context_id: int
    auth_value: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> AuthVerifier:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
