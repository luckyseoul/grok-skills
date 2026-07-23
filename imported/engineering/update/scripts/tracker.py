"""
Background task tracker for the 'update' skill.

Enhanced version with monitor support and better metadata.
"""

import json
import os
import time
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any


STATE_FILE = os.path.expanduser("~/.grok/skills/update/tasks.json")
MAX_TASKS = 60


@dataclass
class BackgroundTask:
    task_id: str
    description: str
    command: Optional[str] = None
    task_type: str = "terminal"  # "terminal", "monitor", "subagent"
    start_time: float = 0.0
    last_checked: float = 0.0
    status: str = "running"
    exit_code: Optional[int] = None
    last_output: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackgroundTask":
        if "metadata" not in data:
            data["metadata"] = {}
        return cls(**data)


def _load_tasks() -> List[BackgroundTask]:
    if not os.path.exists(STATE_FILE):
        return []
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        return [BackgroundTask.from_dict(item) for item in data]
    except Exception:
        return []


def _save_tasks(tasks: List[BackgroundTask]) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tasks = sorted(tasks, key=lambda t: t.start_time, reverse=True)[:MAX_TASKS]
    with open(STATE_FILE, "w") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=2)


def register_background_task(
    task_id: str,
    description: str,
    command: Optional[str] = None,
    task_type: str = "terminal",
    metadata: Optional[Dict[str, Any]] = None,
) -> BackgroundTask:
    """Register a background task (terminal, monitor, or subagent)."""
    tasks = _load_tasks()
    tasks = [t for t in tasks if t.task_id != task_id]

    task = BackgroundTask(
        task_id=task_id,
        description=description,
        command=command,
        task_type=task_type,
        start_time=time.time(),
        last_checked=time.time(),
        status="running",
        metadata=metadata or {},
    )
    tasks.append(task)
    _save_tasks(tasks)
    return task


def register_monitor(
    monitor_id: str,
    description: str,
    command: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> BackgroundTask:
    """Convenience wrapper for registering monitor tool invocations."""
    return register_background_task(
        task_id=monitor_id,
        description=description,
        command=command,
        task_type="monitor",
        metadata=metadata,
    )


def get_recent_tasks(limit: int = 25) -> List[BackgroundTask]:
    tasks = _load_tasks()
    tasks.sort(key=lambda t: t.start_time, reverse=True)
    return tasks[:limit]


def get_task(task_id: str) -> Optional[BackgroundTask]:
    tasks = _load_tasks()
    for t in tasks:
        if t.task_id == task_id:
            return t
    return None


def update_task_output(task_id: str, output: str, status: Optional[str] = None) -> None:
    tasks = _load_tasks()
    for t in tasks:
        if t.task_id == task_id:
            t.last_output = output
            t.last_checked = time.time()
            if status:
                t.status = status
            break
    _save_tasks(tasks)


def mark_task_completed(task_id: str, exit_code: int, final_output: str = "") -> None:
    tasks = _load_tasks()
    for t in tasks:
        if t.task_id == task_id:
            t.status = "completed" if exit_code == 0 else "failed"
            t.exit_code = exit_code
            t.last_output = final_output or t.last_output
            t.last_checked = time.time()
            break
    _save_tasks(tasks)


def mark_task_failed(task_id: str, error: str) -> None:
    tasks = _load_tasks()
    for t in tasks:
        if t.task_id == task_id:
            t.status = "failed"
            t.error = error
            t.last_checked = time.time()
            break
    _save_tasks(tasks)


def get_active_tasks() -> List[BackgroundTask]:
    """Return only tasks that are still considered running."""
    return [t for t in get_recent_tasks(40) if t.status == "running"]