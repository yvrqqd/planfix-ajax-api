import asyncio
import signal

from loguru import logger

from app.application.client_service import ClientService
from app.config.service import SERVICE_CONFIG
from app.infrastructure.browser.browser_session import BrowserSession
from app.infrastructure.persistence.client_repository import ClientRepository
from app.interface.http.server import Server


class Service:
    __slots__ = ('_loop',)

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

    def start(self) -> None:
        shutdown_event = asyncio.Event()

        for sig in (signal.SIGINT, signal.SIGTERM):
            self._loop.add_signal_handler(sig, self._request_shutdown, sig, shutdown_event)

        logger.info("Starting planfix-ajax-api service")

        try:
            self._loop.run_until_complete(self._run_service(shutdown_event))
        finally:
            self._cleanup()

    @staticmethod
    def _request_shutdown(sig: signal.Signals, event: asyncio.Event) -> None:
        if event.is_set():
            logger.warning(f"Received {sig.name} again — forcing shutdown")
            raise SystemExit(1)
        logger.info(f"Received {sig.name}, shutting down gracefully...")
        event.set()

    @staticmethod
    async def _run_service(shutdown_event: asyncio.Event) -> None:
        br = None
        server = None

        try:
            loop = asyncio.get_running_loop()

            br = BrowserSession(loop)
            await br.preconnect(headless=SERVICE_CONFIG.headless)

            repository = ClientRepository()
            client_service = ClientService(
                browser_session=br,
                repository=repository,
                timeout=SERVICE_CONFIG.timeout,
            )

            server = Server(
                host="0.0.0.0",
                port=8000,
                client_service=client_service,
                swagger_enabled=SERVICE_CONFIG.swagger_enabled,
            )
            await server.start()
            logger.info("Service ready — accepting requests on 0.0.0.0:8000")

            await shutdown_event.wait()

        except Exception as err:
            logger.exception(f"Service failed: {err}")

        finally:
            logger.info("Shutting down...")

            if server is not None:
                await server.stop()

            if br is not None:
                await br.close_connection()

            logger.info("Shutdown complete")

    def _cleanup(self) -> None:
        async def _cancel_remaining() -> None:
            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        try:
            self._loop.run_until_complete(_cancel_remaining())
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        finally:
            self._loop.close()
            logger.info("Event loop closed")
