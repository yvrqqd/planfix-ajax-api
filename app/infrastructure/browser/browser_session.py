import asyncio

from loguru import logger
from playwright._impl._connection import Connection
from playwright._impl._object_factory import create_remote_object
from playwright._impl._transport import PipeTransport
from playwright.async_api._generated import Browser, Playwright as AsyncPlaywright


class BrowserSession:
    __slots__ = (
        'connection',
        'async_playwright',
        'browser',
        'loop',
    )

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.connection: Connection | None = None
        self.async_playwright: AsyncPlaywright | None = None
        self.browser: Browser | None = None
        self.loop = loop

    async def preconnect(self, headless: bool = True) -> None:
        logger.info(f"Launching Playwright browser (headless={headless})")

        self.connection = Connection(
            dispatcher_fiber=None,
            object_factory=create_remote_object,
            transport=PipeTransport(self.loop),
            loop=self.loop,
        )

        self.loop.create_task(self.connection.run())
        playwright_future = self.connection.playwright_future

        done, _ = await asyncio.wait(
            {self.connection._transport.on_error_future, playwright_future},  # noqa: WPS437
            return_when=asyncio.FIRST_COMPLETED,
        )

        if not playwright_future.done():
            playwright_future.cancel()

        playwright = AsyncPlaywright(next(iter(done)).result())
        playwright.stop = self.close_connection  # type: ignore[method-assign]

        self.async_playwright = playwright
        self.browser = await self.async_playwright.chromium.launch(headless=headless)
        logger.info("Browser ready")

    async def close_connection(self) -> None:
        logger.info("Closing browser connection...")

        try:
            if self.browser is not None:
                await self.browser.close()
        except Exception as err:
            logger.warning(f"Error closing browser: {err}")

        try:
            if self.connection is not None:
                await self.connection.stop_async()
        except Exception as err:
            logger.warning(f"Error stopping Playwright transport: {err}")

        logger.info("Browser connection closed")
