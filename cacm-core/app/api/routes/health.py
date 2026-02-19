from __future__ import annotations

import socket
import time
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from urllib.parse import urlparse

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])

_STARTED_AT = datetime.now(timezone.utc)
_START_MONO = time.monotonic()


# Health Check Models


class ServiceStatus(str, Enum):
    UP = "up"
    DOWN = "down"


class SystemStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"


class PostgresHealth(BaseModel):
    status: ServiceStatus
    host: str
    port: int
    database: str
    response_ms: float = Field(description="TCP connect time in milliseconds")
    error: str | None = None


class HealthResponse(BaseModel):
    status: SystemStatus
    started_at: datetime
    uptime_seconds: int
    postgres: PostgresHealth


# Health Check Helpers


def _probe_postgres(
    dsn: str,
    timeout: float = 2.0,
) -> PostgresHealth:
    """Open a raw TCP socket to the Postgres host and measure latency."""
    parsed = urlparse(dsn)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    database = parsed.path.lstrip("/") or ""

    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed_ms = (time.perf_counter() - t0) * 1_000
            return PostgresHealth(
                status=ServiceStatus.UP,
                host=host,
                port=port,
                database=database,
                response_ms=round(elapsed_ms, 2),
            )
    except OSError as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1_000
        return PostgresHealth(
            status=ServiceStatus.DOWN,
            host=host,
            port=port,
            database=database,
            response_ms=round(elapsed_ms, 2),
            error=str(exc),
        )


# Routes


@router.get(
    "",
    summary="Aggregate health check",
    response_model=HealthResponse,
)
def health_root(response: Response) -> HealthResponse:
    """
    Returns the overall system health.

    * **200** – all dependencies healthy
    * **503** – one or more dependencies unreachable
    """
    pg = _probe_postgres(str(settings.pg_dsn))

    all_ok = pg.status is ServiceStatus.UP
    if not all_ok:
        response.status_code = 503

    return HealthResponse(
        status=SystemStatus.OK if all_ok else SystemStatus.DEGRADED,
        started_at=_STARTED_AT,
        uptime_seconds=int(time.monotonic() - _START_MONO),
        postgres=pg,
    )


@router.get(
    "/postgres",
    summary="PostgreSQL probe",
    response_model=PostgresHealth,
)
def health_postgres(response: Response) -> PostgresHealth:
    """
    Dedicated Postgres connectivity probe.

    * **200** – reachable
    * **503** – unreachable
    """
    pg = _probe_postgres(str(settings.pg_dsn))
    if pg.status is ServiceStatus.DOWN:
        response.status_code = 503
    return pg
