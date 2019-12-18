class RPCConnection:

    def __init__(self, reader, writer):

        self._read = reader
        self._write = writer

    async def bind(self, presentation_context_list: ContextList, **optional_bind_header_kwargs):
        # TODO: Make the presentation syntaxes into constants.
        await self._write(
            write_data=bytes(
                BindHeader(presentation_context_list=presentation_context_list, **optional_bind_header_kwargs)
            )
        )

        p = BindAckHeader.from_bytes(data=await self._read())

        if not isinstance(p, BindAckHeader):
            raise ValueError



        #
        # q = await self._write(
        #     write_data=bytes(
        #         Request(
        #             call_id=p.call_id,
        #             opnum=15,
        #         )
        #     )
        # )