from pathlib import Path

import connexion
from aiohttp import web
from loguru import logger

from app.application.client_service import ClientService
from app.interface.http import view as view_module
from app.interface.http.view import HTTPView


class Server:
    __slots__ = (
        '_host',
        '_port',
        '_runner',
        '_site',
    )

    def __init__(
            self,
            host: str,
            port: int,
            client_service: ClientService,
            swagger_enabled: bool = False,
    ) -> None:
        http_view = HTTPView(client_service)

        view_module.create_client = http_view.create_client  # type: ignore[attr-defined]
        view_module.list_clients = http_view.list_clients  # type: ignore[attr-defined]
        view_module.delete_client = http_view.delete_client  # type: ignore[attr-defined]
        view_module.run_query = http_view.run_query  # type: ignore[attr-defined]
        view_module.ready_check = http_view.ready_check  # type: ignore[attr-defined]

        spec_dir = str(Path(__file__).parent.parent.resolve())

        cxn_app = connexion.AioHttpApp(
            'app.interface.http.server',
            specification_dir=spec_dir,
        )
        cxn_app.add_api(
            'openapi.yaml',
            base_path='/api',
            options={'swagger_ui': swagger_enabled},
        )

        if swagger_enabled:
            logger.info(f"Swagger UI enabled at http://{host}:{port}/api/ui/")

        self._host: str = host
        self._port: int = port
        self._runner: web.AppRunner = web.AppRunner(app=cxn_app.app)
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        await self._runner.setup()

        self._site = web.TCPSite(
            runner=self._runner,
            host=self._host,
            port=self._port,
            reuse_address=True,
            reuse_port=True,
        )
        await self._site.start()
        logger.info(f"HTTP server listening on {self._host}:{self._port}")

    async def stop(self) -> None:
        logger.info("Stopping HTTP server...")

        if self._site is not None:
            await self._site.stop()

        await self._runner.cleanup()
        logger.info("HTTP server stopped")
