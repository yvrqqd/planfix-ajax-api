import uuid
import base64
from typing import Callable

from loguru import logger


class ServiceStateHolder:
    def get_callback(
            self, name: str | None = None, prefix: str | None = None,
    ) -> Callable[[bool], None]:
        if name is None:
            uuid_bytes = uuid.uuid4().bytes
            name = base64.urlsafe_b64encode(uuid_bytes).rstrip(b'=').decode()

        if prefix is not None:
            name = f"{prefix}{name}"

        if hasattr(self, name):
            raise KeyError("Name already exists")
        setattr(self, name, False)

        def _callback_func(status: bool) -> None:
            setattr(self, name, status)
            logger.info(f"{name} status set to {status}")

        logger.info(f"Registered state callback {name}")
        return _callback_func

    @property
    def is_service_ready(self) -> bool:
        return False not in self.__dict__.values()


SERVICE_STATE: ServiceStateHolder = ServiceStateHolder()
