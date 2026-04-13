from pydantic import SecretStr, BaseModel, Field


class Credentials(BaseModel):
    username: str = Field()
    password: SecretStr = Field()
