from typing import Callable, Awaitable

from rpc.pdu_headers.bind import BindHeader
from rpc.pdu_headers.bind_ack import BindAckHeader
from rpc.structures.context_list import ContextList


class Connection:
    def __init__(self, reader: Callable[[], Awaitable[bytes]], writer: Callable[[bytes], Awaitable[int]]):
        self._read: Callable[[], Awaitable[bytes]] = reader
        self._write: Callable[[bytes], Awaitable[int]] = writer

    async def bind(self, presentation_context_list: ContextList, **optional_bind_header_kwargs):
        await self._write(
            bytes(
                BindHeader(presentation_context_list=presentation_context_list, **optional_bind_header_kwargs)
            )
        )

        p = BindAckHeader.from_bytes(data=await self._read())

        if not isinstance(p, BindAckHeader):
            raise ValueError
