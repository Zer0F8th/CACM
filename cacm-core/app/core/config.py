from collections.abc import Callable
from typing import Annotated, Any

from pydantic import (
    AmqpDsn,
    AnyUrl,
    BeforeValidator,
    ImportString,
    computed_field,
    PostgresDsn,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


# ref: https://docs.pydantic.dev/latest/concepts/pydantic_settings/


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"

    PROJECT_NAME: str = "CACM Core API"

    FRONTEND_HOST: str = "http://localhost:5173"

    pg_dsn: PostgresDsn = (
        "postgres://username:password@localhost:5432/cacm_db?sslmode=disable"
    )

    amqp_dsn: AmqpDsn = "amqp://user:pass@localhost:5672/"

    special_function: ImportString[Callable[[Any], Any]] = "math.cos"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    # to override domains:
    # export my_prefix_domains='["foo.com", "bar.com"]'
    domains: set[str] = set()

    model_config = SettingsConfigDict(env_prefix="my_prefix_")


settings = Settings()  # type: ignore
print(Settings().model_dump())
