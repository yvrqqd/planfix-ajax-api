from app.domain.client import Client
from app.domain.repositories import IClientRepository


class ClientRepository(IClientRepository):
    __slots__ = ('_clients',)

    def __init__(self) -> None:
        self._clients: dict[str, Client] = {}

    def add(self, client: Client) -> None:
        for existing in self._clients.values():
            if existing.login == client.login and existing.domain == client.domain:
                raise ValueError(f"Client with login '{client.login}' already exists")
        self._clients[client.id] = client

    def remove(self, client_id: str) -> Client:
        if client_id not in self._clients:
            raise KeyError(f"Client '{client_id}' not found")
        return self._clients.pop(client_id)

    def get(self, client_id: str) -> Client:
        if client_id not in self._clients:
            raise KeyError(f"Client '{client_id}' not found")
        return self._clients[client_id]

    def list_all(self) -> list[Client]:
        return list(self._clients.values())
