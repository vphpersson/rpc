from __future__ import annotations
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Dict, Type, ClassVar, Optional
from contextlib import suppress

from rpc.connection import Connection as RPCConnection
from rpc.pdu_headers.base import MSRPCHeader
from rpc.pdu_headers.request_header import RequestHeader
from rpc.pdu_headers.response_header import ResponseHeader


class NoMatchingErrorClassError(Exception):
    def __init__(self, return_code: IntEnum):
        super().__init__(f'The return code {return_code} does not map to any error class.')
        self.return_code = return_code


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
        try:
            return cls.RETURN_CODE_TO_ERROR_CLASS[response.return_code](response=response)
        except KeyError as e:
            raise NoMatchingErrorClassError(return_code=response.return_code) from e


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

    response_error: Optional[ClientProtocolResponseError] = None
    # Only return codes indicating errors map to an error class. Return codes for successes result in a lookup error.
    with suppress(NoMatchingErrorClassError):
        response_error = client_protocol_response.ERROR_CLASS.from_response(response=client_protocol_response)

    if raise_exception and response_error is not None:
        raise response_error

    return client_protocol_response
