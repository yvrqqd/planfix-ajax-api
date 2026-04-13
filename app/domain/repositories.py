from abc import ABC, abstractmethod

from app.domain.client import Client


class IClientRepository(ABC):
    @abstractmethod
    def add(self, client: Client) -> None: ...

    @abstractmethod
    def remove(self, client_id: str) -> Client: ...

    @abstractmethod
    def get(self, client_id: str) -> Client: ...

    @abstractmethod
    def list_all(self) -> list[Client]: ...
