from __future__ import annotations
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Dict, Type, ClassVar

from rpc.connection import Connection as RPCConnection
from rpc.pdu_headers.base import MSRPCHeader
from rpc.pdu_headers.request_header import RequestHeader
from rpc.pdu_headers.response_header import ResponseHeader


class ClientProtocolMessage(ABC):
    @abstractmethod
    def __bytes__(self) -> bytes:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_bytes(cls, data: bytes) -> ClientProtocolMessage:
        raise NotImplementedError


class ClientProtocolRequestBase(ClientProtocolMessage, ABC):
    OPERATION: IntEnum = NotImplemented
    RESPONSE_CLASS: Type[ClientProtocolResponseBase] = NotImplemented


@dataclass
class ClientProtocolResponseBase(ClientProtocolMessage, ABC):
    REQUEST_CLASS: ClassVar[Type[ClientProtocolRequestBase]] = NotImplemented
    ERROR_CLASS: ClassVar[Type[ClientProtocolResponseError]] = NotImplemented
    return_code: IntEnum


class ClientProtocolResponseError(Exception, ABC):
    RETURN_CODE: IntEnum = NotImplemented
    DESCRIPTION: str = NotImplemented
    RETURN_CODE_TO_ERROR_CLASS: Dict[IntEnum, Type[ClientProtocolResponseError]] = NotImplemented

    def __init__(self, response: ClientProtocolResponseBase):
        super().__init__(self.DESCRIPTION)
        self.response: ClientProtocolResponseBase = response

    @classmethod
    def from_response(cls, response: ClientProtocolResponseBase) -> ClientProtocolResponseError:
        return cls.RETURN_CODE_TO_ERROR_CLASS[response.return_code](response=response)


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

    # NOTE: It seems that I must use the integer value of the return code to have this function be general.
    if client_protocol_response.return_code.value != 0 and raise_exception:
        raise client_protocol_response.ERROR_CLASS.from_response(response=client_protocol_response)

    return client_protocol_response
