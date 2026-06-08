"""FastAPI server exposing the storyboard pipeline to the frontend."""
from __future__ import annotations

import asyncio
import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.paths import ENV_FILE, FRONTEND_DIST, IMAGES_DIR
from backend.system.pipeline import run_pipeline, run_plan

load_dotenv(ENV_FILE)

for _proxy_var in (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
):
    os.environ.pop(_proxy_var, None)

GenerationMode = Literal["simple", "agentic"]
TaskStatus = Literal["pending", "planning", "generating", "merging", "done", "error"]


@dataclass
class TaskRecord:
    task_id: str
    status: TaskStatus = "pending"
    message: str = "任务已创建"
    percent: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    plan: Optional[Dict[str, Any]] = None
    images: List[Dict[str, Any]] = field(default_factory=list)
    agent_result: Optional[Dict[str, Any]] = None
    storyboard_url: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    events: List[Dict[str, Any]] = field(default_factory=list)
    _event: threading.Event = field(default_factory=threading.Event, repr=False)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "message": self.message,
            "percent": self.percent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "plan": self.plan,
            "images": self.images,
            "agent_result": self.agent_result,
            "storyboard_url": self.storyboard_url,
            "result": self.result,
            "error": self.error,
        }

    def push_event(self, payload: Dict[str, Any]) -> None:
        self.events.append(payload)
        self._event.set()
        self._event = threading.Event()


class PlanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    shot_count: int = Field(default=3, ge=1, le=8)


class GenerateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    shot_count: int = Field(default=3, ge=1, le=8)
    mode: GenerationMode = "simple"
    config: Dict[str, Any] = Field(default_factory=dict)


class TaskStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = threading.Lock()

    def create(self) -> TaskRecord:
        task_id = str(uuid.uuid4())
        record = TaskRecord(task_id=task_id)
        with self._lock:
            self._tasks[task_id] = record
        return record

    def get(self, task_id: str) -> TaskRecord:
        with self._lock:
            record = self._tasks.get(task_id)
        if record is None:
            raise KeyError(task_id)
        return record


task_store = TaskStore()
app = FastAPI(title="AI Director Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _map_stage_to_status(stage: str) -> TaskStatus:
    if stage == "planning":
        return "planning"
    if stage in {"generating", "shot_done", "agent_done"}:
        return "generating"
    if stage == "merging":
        return "merging"
    if stage == "done":
        return "done"
    return "generating"


def _apply_progress(record: TaskRecord, payload: Dict[str, Any]) -> None:
    stage = str(payload.get("stage", ""))
    record.updated_at = _utc_now()
    record.message = str(payload.get("message", record.message))
    record.percent = int(payload.get("percent", record.percent))
    record.status = _map_stage_to_status(stage)

    if payload.get("plan") is not None:
        record.plan = payload["plan"]
    if payload.get("images"):
        record.images.extend(payload["images"])
    if payload.get("agent_result") is not None:
        record.agent_result = payload["agent_result"]
    if payload.get("result") is not None:
        result = payload["result"]
        record.result = result
        record.plan = result.get("plan", record.plan)
        record.images = result.get("images", record.images)
        record.agent_result = result.get("agent_result", record.agent_result)
        record.storyboard_url = result.get("storyboard_url")
        record.status = "done"
        record.percent = 100


def _run_task(record: TaskRecord, request: GenerateRequest) -> None:
    try:
        def on_progress(payload: Dict[str, Any]) -> None:
            _apply_progress(record, payload)
            record.push_event(payload)

        result = run_pipeline(
            request.text,
            task_id=record.task_id,
            shot_count=request.shot_count,
            mode=request.mode,
            config_overrides=request.config or None,
            on_progress=on_progress,
        )
        _apply_progress(record, {"stage": "done", "percent": 100, "result": result, "message": "完成"})
        record.push_event({"stage": "done", "percent": 100, "result": result, "message": "完成"})
    except Exception as exc:  # noqa: BLE001
        record.status = "error"
        record.error = str(exc)
        record.message = f"生成失败: {exc}"
        record.updated_at = _utc_now()
        record.push_event({"stage": "error", "error": str(exc), "message": record.message})


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/plan")
def create_plan(request: PlanRequest) -> Dict[str, Any]:
    try:
        return run_plan(request.text, shot_count=request.shot_count)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/generate")
def create_generate_task(request: GenerateRequest) -> Dict[str, str]:
    record = task_store.create()
    worker = threading.Thread(
        target=_run_task,
        args=(record, request),
        daemon=True,
        name=f"storyboard-{record.task_id}",
    )
    worker.start()
    return {"task_id": record.task_id}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> Dict[str, Any]:
    try:
        return task_store.get(task_id).snapshot()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@app.get("/api/tasks/{task_id}/events")
async def stream_task_events(task_id: str):
    try:
        record = task_store.get(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc

    async def event_generator():
        sent = 0
        while True:
            while sent < len(record.events):
                payload = record.events[sent]
                sent += 1
                yield {
                    "event": str(payload.get("stage", "progress")),
                    "data": json.dumps(payload, ensure_ascii=False),
                }
                if payload.get("stage") in {"done", "error"}:
                    return

            if record.status in {"done", "error"}:
                return

            wait_event = record._event
            await asyncio.to_thread(wait_event.wait, 300)
            if record.status in {"done", "error"} and sent >= len(record.events):
                return

    return EventSourceResponse(event_generator())


@app.get("/api/images/{task_id}/{filename}")
def get_task_image(task_id: str, filename: str):
    safe_name = Path(filename).name
    if safe_name != filename or ".." in task_id or "/" in task_id or "\\" in task_id:
        raise HTTPException(status_code=400, detail="Invalid image path")

    image_path = IMAGES_DIR / task_id / safe_name
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")


@app.get("/api/images/legacy/{filename}")
def get_legacy_image(filename: str):
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    candidates = sorted(IMAGES_DIR.rglob(safe_name), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(candidates[0], media_type="image/png")


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
