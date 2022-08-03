from __future__ import annotations
from typing import Callable, Awaitable, Iterator
from asyncio import Queue as AsyncioQueue, Task, create_task, Future
from itertools import count as itertools_count

from rpc.pdu_headers.base import MSRPCHeader
from rpc.pdu_headers.bind import BindHeader
from rpc.pdu_headers.bind_ack import BindAckHeader
from rpc.structures.context_list import ContextList


class Connection:
    def __init__(self, reader: Callable[[], Awaitable[bytes]], writer: Callable[[bytes], Awaitable[int]]):
        self._read: Callable[[], Awaitable[bytes]] = reader
        self._write: Callable[[bytes], Awaitable[int]] = writer

        self._receive_message_responses_task: Task | None = None
        self._handle_incoming_bytes_task: Task | None = None
        self._handle_outgoing_bytes_task: Task | None = None

        # Data structures for handling incoming and outgoing messages.
        self._incoming_messages_queue = AsyncioQueue()
        self._outgoing_messages_queue = AsyncioQueue()

        self.call_id_iterator: Iterator[int] = itertools_count(start=1)
        self._outstanding_message_call_id_to_future: dict[int, Future] = {}

    async def bind(self, presentation_context_list: ContextList, **optional_bind_header_kwargs) -> BindAckHeader:
        """
        Perform the RPC binding operation.

        :param presentation_context_list:
        :param optional_bind_header_kwargs:
        :return:
        """

        bind_response: MSRPCHeader = await (
            await self.send_message(
                BindHeader(
                    presentation_context_list=presentation_context_list, **optional_bind_header_kwargs
                )
            )
        )

        if not isinstance(bind_response, BindAckHeader):
            # TODO: Use proper exception.
            raise ValueError

        return bind_response

    async def send_message(self, message: MSRPCHeader, assign_call_id: bool = True) -> Awaitable[MSRPCHeader]:
        """
        Send an RPC message.

        :param message: The message to be sent.
        :param assign_call_id: Whether to assign a call id to the message.
        :return: A `Future` that will resolve to the response to the message sent.
        """

        if assign_call_id:
            message.call_id = next(self.call_id_iterator)

        response_message_future = Future()
        self._outstanding_message_call_id_to_future[message.call_id] = response_message_future
        create_task(self._outgoing_messages_queue.put(message))

        return response_message_future

    async def _receive_message_responses(self) -> None:
        """Receive message responses and resolve the corresponding future."""

        while True:
            incoming_message: MSRPCHeader = await self._incoming_messages_queue.get()
            self._outstanding_message_call_id_to_future.pop(incoming_message.call_id).set_result(incoming_message)

    async def _handle_outgoing_bytes(self) -> None:
        """Serialize outgoing messages and write them."""

        while True:
            await self._write(bytes(await self._outgoing_messages_queue.get()))

    async def _handle_incoming_bytes(self) -> None:
        """Read and deserialize incoming bytes into a message and put it in a queue."""

        while True:
            await self._incoming_messages_queue.put(MSRPCHeader.from_bytes(data=await self._read()))

    async def __aenter__(self) -> Connection:
        self._receive_message_responses_task = create_task(coro=self._receive_message_responses())
        self._handle_incoming_bytes_task = create_task(coro=self._handle_incoming_bytes())
        self._handle_outgoing_bytes_task = create_task(coro=self._handle_outgoing_bytes())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # TODO: Consider order.
        self._handle_incoming_bytes_task.cancel()
        self._handle_outgoing_bytes_task.cancel()
        self._receive_message_responses_task.cancel()
