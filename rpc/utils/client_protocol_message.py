from __future__ import annotations
from dataclasses import dataclass
from abc import ABC
from enum import IntEnum
from typing import Type, ClassVar, Optional, Union, ByteString, Any
from contextlib import suppress
from struct import Struct

from msdsalgs.win32_error import Win32Error, Win32ErrorCode

from rpc.connection import Connection as RPCConnection
from rpc.pdu_headers.base import MSRPCHeader
from rpc.pdu_headers.request_header import RequestHeader
from rpc.pdu_headers.response_header import ResponseHeader
from rpc.utils import unpack_structure, pack_structure


class ClientProtocolMessage(ABC):

    def __bytes__(self) -> bytes:
        if structure := getattr(self, '_STRUCTURE', None):
            return pack_structure(instance=self, structure=structure)
        else:
            raise NotImplementedError

    @classmethod
    def from_bytes(cls, data: Union[ByteString, memoryview], offset: int = 0) -> ClientProtocolMessage:

        if structure := getattr(cls, '_STRUCTURE', None):
            cls_kwargs: dict[str, Any] = unpack_structure(data=data, structure=structure, offset=offset)
            delete_keys = [kwarg_name for kwarg_name in cls_kwargs if kwarg_name.startswith('__')]
            for delete_key in delete_keys:
                del cls_kwargs[delete_key]
            return cls(**cls_kwargs)
        else:
            raise NotImplementedError


class ClientProtocolRequestBase(ClientProtocolMessage, ABC):
    OPERATION: IntEnum = NotImplemented
    RESPONSE_CLASS: Type[ClientProtocolResponseBase] = NotImplemented


@dataclass
class ClientProtocolResponseBase(ClientProtocolMessage, ABC):
    REQUEST_CLASS: ClassVar[Type[ClientProtocolRequestBase]] = NotImplemented
    return_code: Win32ErrorCode

    _RETURN_CODE_STRUCT: ClassVar[Struct] = Struct('<I')


async def obtain_response(
    rpc_connection: RPCConnection,
    request: ClientProtocolRequestBase,
    raise_exception: bool = True
) -> ClientProtocolResponseBase:
    """

    :param rpc_connection: The RPC connection with which to send the message.
    :param request: The client protocol request to send.
    :param raise_exception: Whether to raise an exception in case the client response message's return code indicates
        error.
    :return: The client protocol response message corresponding to the request.
    """

    rpc_response: MSRPCHeader = await (
        await rpc_connection.send_message(
            message=RequestHeader(
                opnum=request.OPERATION.value,
                stub_data=bytes(request)
            )
        )
    )

    if not isinstance(rpc_response, ResponseHeader):
        # TODO: Use proper exception.
        raise ValueError

    client_protocol_response: ClientProtocolResponseBase = request.RESPONSE_CLASS.from_bytes(data=rpc_response.stub_data)
    if not isinstance(client_protocol_response, request.RESPONSE_CLASS):
        # TODO: Use proper exception
        raise ValueError

    response_error: Optional[Win32Error] = None
    # Only return codes indicating errors map to an error class. Return codes for successes result in a lookup error.
    with suppress(KeyError):
        response_error = Win32Error.from_win32_error_code(
            win32_error_code=client_protocol_response.return_code,
            response=client_protocol_response
        )

    if raise_exception and response_error is not None:
        raise response_error

    return client_protocol_response
