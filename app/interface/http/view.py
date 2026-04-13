from aiohttp import web
from loguru import logger
from pydantic import SecretStr

from app.application.client_service import ClientService
from app.utils.service_state import SERVICE_STATE
from app.utils.types import JSONLikeValue


class HTTPView:
    __slots__ = (
        '_client_service',
    )

    def __init__(
            self,
            client_service: ClientService,
    ) -> None:
        self._client_service: ClientService = client_service

    async def create_client(self, body: dict[str, str]) -> web.Response:
        try:
            logger.debug(f"create_client fields: {list(body.keys())}")

            login: str = body['login']
            password: SecretStr = SecretStr(body['password'])
            domain: str = body['domain']

            client = await self._client_service.create_client(
                login=login,
                password=password,
                domain=domain,
            )
            return web.json_response(
                {'id': client.id, 'login': client.login, 'domain': client.domain},
                status=201,
            )
        except KeyError as err:
            logger.warning(f"create_client missing field: {err}")
            return web.json_response({'error': f'Missing field: {err}'}, status=400)
        except ValueError as err:
            logger.warning(f"create_client conflict: {err}")
            return web.json_response({'error': str(err)}, status=409)
        except Exception as err:
            logger.exception(f"create_client failed: {err}")
            return web.json_response({'error': str(err)}, status=500)

    async def list_clients(self) -> web.Response:
        clients = self._client_service.list_clients()
        logger.debug(f"Listing clients ({len(clients)} total)")
        return web.json_response([
            {'id': client.id, 'login': client.login, 'domain': client.domain}
            for client in clients
        ])

    async def delete_client(self, client_id: str) -> web.Response:
        try:
            self._client_service.delete_client(client_id)
            logger.info(f"Client '{client_id}' deleted via API")
            return web.Response(status=204)
        except KeyError:
            logger.warning(f"Delete failed: client '{client_id}' not found")
            return web.json_response({'error': f"Client '{client_id}' not found"}, status=404)

    async def run_query(self, body: dict[str, JSONLikeValue]) -> web.Response:
        try:
            client_id = str(body['client_id'])
            payload: JSONLikeValue = body['payload']
        except KeyError as err:
            logger.warning(f"run_query missing field: {err}")
            return web.json_response({'error': f'Missing field: {err}'}, status=400)

        try:
            executor = self._client_service.get_executor(client_id)
        except KeyError as err:
            logger.warning(f"run_query client not found: {err}")
            return web.json_response({'error': str(err)}, status=404)

        try:
            planfix_response = await executor.execute(payload)
            return web.json_response(planfix_response)
        except Exception as err:
            logger.exception(f"run_query failed: {err}")
            return web.json_response({'error': str(err)}, status=500)

    @classmethod
    async def ready_check(cls) -> web.Response:
        status: int = 200 if SERVICE_STATE.is_service_ready else 404
        return web.Response(status=status)
