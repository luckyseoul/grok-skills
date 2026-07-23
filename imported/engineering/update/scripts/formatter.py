"""
formatter.py - Maximum power, zero-dependency rich formatting for /update output.

Produces beautiful, scannable status reports using:
- Markdown structure the TUI renders nicely
- Careful ANSI colors (only when safe)
- Card-style and table layouts
- Smart excerpting that actually helps during ION/DTN runs
- Duration + age calculations that don't lie
"""

import os
import re
import time
from typing import List, Optional, Dict, Any

from .tracker import BackgroundTask


# --- ANSI (safe, opt-in) -----------------------------------------------------

def _supports_ansi() -> bool:
    # Common signals that we are in a modern terminal / TUI
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    term = os.environ.get("TERM", "")
    return "color" in term or "xterm" in term or "screen" in term or "tmux" in term


ANSI = _supports_ansi()

C = {
    "reset": "\033[0m" if ANSI else "",
    "bold": "\033[1m" if ANSI else "",
    "dim": "\033[2m" if ANSI else "",
    "green": "\033[32m" if ANSI else "",
    "yellow": "\033[33m" if ANSI else "",
    "red": "\033[31m" if ANSI else "",
    "cyan": "\033[36m" if ANSI else "",
    "blue": "\033[34m" if ANSI else "",
    "magenta": "\033[35m" if ANSI else "",
}


def _color(text: str, color: str) -> str:
    code = C.get(color, "")
    if not code:
        return text
    return f"{code}{text}{C['reset']}"


# --- Duration ---------------------------------------------------------------

def format_duration(seconds: float, compact: bool = False) -> str:
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return f"{int(seconds)}s"
    m = int(seconds // 60)
    s = int(seconds % 60)
    if compact or m < 60:
        return f"{m}m {s}s"
    h = m // 60
    m = m % 60
    return f"{h}h {m}m"


def age_str(start_time: float) -> str:
    return format_duration(time.time() - start_time)


# --- Status -----------------------------------------------------------------

def status_badge(task: BackgroundTask, live_status: Optional[Dict] = None) -> str:
    """Return a nice emoji + colored label."""
    s = (live_status or {}).get("status") or task.status or "running"

    if s == "completed" or (live_status and live_status.get("status") == "completed"):
        return _color("✅ completed", "green")
    if s == "failed" or task.error or (live_status and live_status.get("error")):
        return _color("❌ failed", "red")
    if s == "running":
        return _color("⏳ running", "yellow")
    return _color(f"❓ {s}", "dim")


def task_type_icon(t: str) -> str:
    if t == "monitor":
        return "📡"
    if t == "subagent":
        return "🤖"
    return "🖥️"


# --- Excerpts ---------------------------------------------------------------

def smart_excerpt(text: str, max_lines: int = 6, max_chars: int = 900) -> str:
    """Keep the last N meaningful lines. Strip noise. Perfect for ION logs."""
    if not text:
        return ""

    lines = [ln.rstrip() for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return ""

    # Prefer recent + interesting lines (skip pure noise)
    noise = ("DEBUG", "TRACE", "keepalive", "heartbeat", "ping", ".")
    interesting = [ln for ln in lines if not any(n.lower() in ln.lower() for n in noise)]

    chosen = (interesting or lines)[-max_lines:]
    out = "\n".join(chosen)

    if len(out) > max_chars:
        out = "..." + out[-max_chars:]
    return out


# --- Core formatters --------------------------------------------------------

def format_task_row(task: BackgroundTask, poll: Optional[Dict[str, Any]] = None) -> str:
    """One-line row used in summary tables."""
    poll = poll or {}
    badge = status_badge(task, poll)
    age = age_str(task.start_time)
    icon = task_type_icon(task.task_type)

    desc = task.description
    if len(desc) > 58:
        desc = desc[:55] + "…"

    # Latest line of live or cached output
    output = poll.get("output") or task.last_output or ""
    latest = ""
    if output:
        last_line = output.strip().splitlines()[-1][:62]
        latest = last_line

    return f"{icon} {badge}  {age:>8}  | {desc}  `{latest}`"


def format_summary_header(tasks: List[BackgroundTask]) -> str:
    running = sum(1 for t in tasks if t.status == "running")
    failed = sum(1 for t in tasks if t.status == "failed")
    completed = sum(1 for t in tasks if t.status == "completed")

    parts = []
    if running:
        parts.append(_color(f"{running} running", "yellow"))
    if failed:
        parts.append(_color(f"{failed} failed", "red"))
    if completed:
        parts.append(f"{completed} done")

    if not parts:
        return "No active background work."
    return " • ".join(parts)


def format_table(tasks: List[BackgroundTask], max_rows: int = 18) -> str:
    """Pretty markdown table + status."""
    if not tasks:
        return "No tracked background tasks."

    header = "|   | Status          | Age      | Description                                      | Latest line |"
    sep =    "|---|-----------------|----------|--------------------------------------------------|-------------|"

    rows = []
    now = time.time()
    for t in tasks[:max_rows]:
        poll = {}  # caller usually does live poll before calling
        badge = status_badge(t, poll).replace(_color("", ""), "")  # strip for table width
        age = format_duration(now - t.start_time, compact=True)
        icon = task_type_icon(t.task_type)

        desc = t.description[:46] + "…" if len(t.description) > 46 else t.description
        latest = ""
        out = (t.last_output or "")[-400:]
        if out:
            latest = out.strip().splitlines()[-1][:48].replace("|", "│")

        rows.append(f"| {icon} | {badge:<15} | {age:>8} | {desc:<48} | `{latest}` |")

    table = "\n".join([header, sep] + rows)
    return table


def format_detailed_task(task: BackgroundTask, poll: Optional[Dict[str, Any]] = None) -> str:
    """Full card view for `/update <task_id>` or a specific one."""
    poll = poll or {}
    lines = []

    icon = task_type_icon(task.task_type)
    badge = status_badge(task, poll)

    lines.append(f"### {icon} {task.description}")
    lines.append(f"**ID:** `{task.task_id}`   •   **Type:** {task.task_type}   •   **Age:** {age_str(task.start_time)}   •   **Status:** {badge}")

    if task.command:
        lines.append(f"**Command:** `{task.command}`")

    # Live or last output
    live_out = poll.get("output") or ""
    cached = task.last_output or ""

    if live_out:
        excerpt = smart_excerpt(live_out, max_lines=9, max_chars=1400)
        lines.append(f"\n**Live output** ({len(live_out)} chars):\n```\n{excerpt}\n```")
    elif cached:
        excerpt = smart_excerpt(cached, max_lines=7, max_chars=1100)
        lines.append(f"\n**Last known output**:\n```\n{excerpt}\n```")

    if task.error:
        lines.append(f"\n**Error:** {_color(task.error, 'red')}")

    if poll.get("exit_code") is not None:
        ec = poll["exit_code"]
        color = "green" if ec == 0 else "red"
        lines.append(f"**Exit code:** {_color(str(ec), color)}")

    if task.metadata:
        meta = {k: v for k, v in task.metadata.items() if k not in ("output", "stderr")}
        if meta:
            lines.append(f"\n**Metadata:** {meta}")

    return "\n".join(lines)


def format_watch_header(iteration: int = 0) -> str:
    ts = time.strftime("%H:%M:%S")
    return f"\n{_color('👁️  WATCH MODE', 'cyan')} — updated {ts} (iteration {iteration}) — press Ctrl-C or run normal `/update` to stop"


def format_everything(tasks: List[BackgroundTask], show_all: bool = False) -> str:
    """The big report used by /update and /update all."""
    if not tasks:
        return (
            "No background tasks tracked yet.\n\n"
            "**Rule:** After any `run_terminal_command(..., background=True)` or `monitor(...)` call:\n"
            "```python\n"
            "from update import register_background_task, register_monitor\n"
            "register_background_task(task_id=the_id, description=\"what I just started\")\n"
            "```\n"
        )

    out = ["## Background Task Status\n"]
    out.append(format_summary_header(tasks) + "\n")

    running = [t for t in tasks if t.status == "running"]
    failed = [t for t in tasks if t.status == "failed"]
    done = [t for t in tasks if t.status == "completed"]

    if running:
        out.append(f"\n### ⏳ Running ({len(running)})\n")
        for t in running:
            out.append("• " + format_task_row(t))

    if failed:
        out.append(f"\n### ❌ Failed ({len(failed)})\n")
        for t in failed:
            out.append("• " + format_task_row(t))

    recent_done = done[:8] if not show_all else done
    if recent_done:
        out.append(f"\n### ✅ Recently completed ({len(recent_done)} shown)\n")
        for t in recent_done:
            out.append("• " + format_task_row(t))

    total = len(tasks)
    shown = len(running) + len(failed) + len(recent_done)
    if total > shown:
        out.append(f"\n_{total - shown} more tasks hidden. Use `/update all`._")

    out.append("\n**Tip:** `/update <task_id>` for full live output of one task. `/update --watch` for continuous view.")
    return "\n".join(out)
