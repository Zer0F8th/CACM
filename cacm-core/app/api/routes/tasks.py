from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel

from app.worker.celery_app import celery
from app.worker.tasks import collect_baseline, compare_baselines, normalize_baseline

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ── Request / Response Schemas ──────────────────────────────────────


class CollectRequest(BaseModel):
    asset_id: str
    host: str
    port: int = 22
    username: str = "cacm_collector"
    password: str = "collector"


class NormalizeRequest(BaseModel):
    asset_id: str
    collection_id: str


class CompareRequest(BaseModel):
    asset_id: str
    baseline_a_id: str
    baseline_b_id: str


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None


class ScheduledTask(BaseModel):
    name: str
    task: str
    schedule: str
    args: list | None = None


# ── Routes ──────────────────────────────────────────────────────────


@router.post(
    "/collect",
    summary="Submit a baseline collection job",
    response_model=TaskSubmitResponse,
    status_code=202,
)
def submit_collect(body: CollectRequest) -> TaskSubmitResponse:
    result = collect_baseline.delay(
        body.asset_id, body.host, body.port, body.username, body.password
    )
    return TaskSubmitResponse(task_id=result.id, status="PENDING")


@router.post(
    "/normalize",
    summary="Submit a baseline normalization job",
    response_model=TaskSubmitResponse,
    status_code=202,
)
def submit_normalize(body: NormalizeRequest) -> TaskSubmitResponse:
    result = normalize_baseline.delay(body.asset_id, body.collection_id)
    return TaskSubmitResponse(task_id=result.id, status="PENDING")


@router.post(
    "/compare",
    summary="Submit a baseline comparison job",
    response_model=TaskSubmitResponse,
    status_code=202,
)
def submit_compare(body: CompareRequest) -> TaskSubmitResponse:
    result = compare_baselines.delay(
        body.asset_id, body.baseline_a_id, body.baseline_b_id
    )
    return TaskSubmitResponse(task_id=result.id, status="PENDING")


@router.get(
    "/{task_id}",
    summary="Check task status",
    response_model=TaskStatusResponse,
)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Query the state of a previously submitted task.

    Possible statuses: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED.
    """
    ar = AsyncResult(task_id, app=celery)
    response = TaskStatusResponse(task_id=task_id, status=ar.status)

    if ar.status == "SUCCESS":
        response.result = ar.result
    elif ar.status == "FAILURE":
        response.error = str(ar.result)

    return response


@router.get(
    "/scheduled/list",
    summary="List periodic (Beat) tasks",
    response_model=list[ScheduledTask],
)
def list_scheduled_tasks() -> list[ScheduledTask]:
    """Return all Celery Beat scheduled tasks."""
    tasks: list[ScheduledTask] = []
    for name, entry in celery.conf.beat_schedule.items():
        tasks.append(
            ScheduledTask(
                name=name,
                task=entry["task"],
                schedule=str(entry["schedule"]),
                args=entry.get("args"),
            )
        )
    return tasks
