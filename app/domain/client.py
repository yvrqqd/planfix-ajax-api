import uuid

from pydantic import BaseModel, Field


class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    login: str = Field()
    domain: str = Field()
