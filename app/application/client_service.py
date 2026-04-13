from pydantic import SecretStr
from loguru import logger

from app.domain.client import Client
from app.domain.credentials import Credentials
from app.domain.repositories import IClientRepository
from app.infrastructure.browser.browser_session import BrowserSession
from app.infrastructure.browser.session import Session
from app.infrastructure.planfix.query_executor import QueryExecutor


class ClientService:
    __slots__ = (
        '_browser_session',
        '_repository',
        '_timeout',
        '_sessions',
        '_executors',
    )

    def __init__(
            self,
            browser_session: BrowserSession,
            repository: IClientRepository,
            timeout: float = 30000.0,
    ) -> None:
        self._browser_session: BrowserSession = browser_session
        self._repository: IClientRepository = repository
        self._timeout: float = timeout
        self._sessions: dict[str, Session] = {}
        self._executors: dict[str, QueryExecutor] = {}

    async def create_client(self, login: str, password: SecretStr, domain: str) -> Client:
        client = Client(login=login, domain=domain)
        self._repository.add(client)

        try:
            credentials = Credentials(username=login, password=password)
            session = Session(
                domain=domain,
                credentials=credentials,
                browser_session=self._browser_session,
                timeout=self._timeout,
            )
            await session.create()

            executor = QueryExecutor(domain=domain, session=session)

            self._sessions[client.id] = session
            self._executors[client.id] = executor

            logger.info(f"Client '{client.login}' created with id '{client.id}'")
        except Exception:
            self._repository.remove(client.id)
            raise

        return client

    def delete_client(self, client_id: str) -> None:
        client = self._repository.remove(client_id)
        self._sessions.pop(client_id, None)
        self._executors.pop(client_id, None)
        logger.info(f"Client '{client.login}' deleted")

    def list_clients(self) -> list[Client]:
        return self._repository.list_all()

    def get_executor(self, client_id: str) -> QueryExecutor:
        if client_id not in self._executors:
            raise KeyError(f"No executor for client '{client_id}'")
        return self._executors[client_id]
