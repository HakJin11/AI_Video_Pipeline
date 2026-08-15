import asyncio
import uuid
from typing import Any, Callable

_jobs: dict[str, dict[str, Any]] = {}


def create_job() -> str:
    job_id = uuid.uuid4().hex
    _jobs[job_id] = {"status": "queued", "result": None, "error": None}
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


async def run_job(job_id: str, fn: Callable[..., Any], *args: Any) -> None:
    _jobs[job_id]["status"] = "running"
    try:
        result = await asyncio.to_thread(fn, *args)
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["result"] = result
    except Exception as exc:  # noqa: BLE001 - surface any failure to the polling client
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(exc)


def start_job(fn: Callable[..., Any], *args: Any) -> str:
    job_id = create_job()
    asyncio.create_task(run_job(job_id, fn, *args))
    return job_id
