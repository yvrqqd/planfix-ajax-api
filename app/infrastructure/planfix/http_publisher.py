import aiohttp


class HTTPPublisher:
    __slots__ = (
        '_connection',
    )

    def __init__(self) -> None:
        self._connection: aiohttp.ClientSession | None = None

    async def setup_connection(self) -> None:
        if self._connection is not None:
            await self._connection.close()

        self._connection = aiohttp.ClientSession()

    async def close_connection(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
