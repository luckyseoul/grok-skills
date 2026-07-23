"""
update skill — Turned Up to 11 (Maximum Overdrive)

Nuclear-grade background task observability.
Auto-discovers forgotten tasks, gives gorgeous live status, and never lets you lose track of ION nodes, monitors, or huge compiles again.
"""

import time
from typing import List, Optional, Dict, Any

from .tracker import (
    get_recent_tasks,
    get_task,
    register_background_task,
    register_monitor,
    BackgroundTask,
    update_task_output,
    mark_task_completed,
    mark_task_failed,
)
from .conversation_scanner import (
    scan_for_tasks,
    extract_task_ids_only,
)
from .formatter import (
    format_everything,
    format_detailed_task,
    format_summary_header,
    format_table,
    format_task_row,
    format_watch_header,
    age_str,
    smart_excerpt,
)

try:
    from tools import get_command_or_subagent_output
except ImportError:
    try:
        from grok_tools import get_command_or_subagent_output
    except ImportError:
        get_command_or_subagent_output = None


def _poll(task: BackgroundTask, block: bool = False) -> Optional[Dict[str, Any]]:
    """Safely poll the platform for fresh status + output of a background task."""
    if not get_command_or_subagent_output:
        return None
    try:
        result = get_command_or_subagent_output(task_id=task.task_id, block=block)
        # Side-effect: keep our local mirror fresh
        if result:
            if result.get("output"):
                update_task_output(task.task_id, result["output"][-4000:])
            if result.get("status") == "completed":
                mark_task_completed(
                    task.task_id,
                    result.get("exit_code", 0),
                    result.get("output", "")[-4000:],
                )
            elif result.get("error"):
                mark_task_failed(task.task_id, result["error"])
        return result
    except Exception as e:
        return {"error": str(e)}


def handle_update(
    args: Optional[str] = None,
    recent_messages: Optional[List[str]] = None,
) -> str:
    """
    The single entry point called by the TUI when the user types /update ...

    This version is deliberately aggressive about discovery and beautiful output.
    """
    # 1. Start from persisted tasks
    tasks = get_recent_tasks(limit=120)

    # 2. Nuclear auto-discovery from the conversation itself
    newly_registered = 0
    if recent_messages:
        # High-quality discovery (with descriptions and type hints)
        discovered = scan_for_tasks(recent_messages, max_tasks=25, min_confidence=0.4)

        for d in discovered:
            if not get_task(d.task_id):
                register_background_task(
                    task_id=d.task_id,
                    description=d.description,
                    task_type=d.task_type,
                )
                newly_registered += 1

        # Also run the cheap ID-only pass as a safety net
        cheap_ids = extract_task_ids_only(recent_messages, limit=30)
        for tid in cheap_ids:
            if not get_task(tid):
                register_background_task(
                    task_id=tid,
                    description="Auto-discovered background task (fallback)",
                    task_type="terminal",
                )
                newly_registered += 1

        if newly_registered:
            tasks = get_recent_tasks(limit=120)

    if not tasks:
        return (
            "No background tasks tracked yet.\n\n"
            "**Golden rule:** Right after you call `run_terminal_command(..., background=True)` or `monitor(...)`:\n"
            "```python\n"
            "from update import register_background_task, register_monitor\n"
            "register_background_task(task_id=the_id_you_just_got, description=\"ION node start - soulkiller contacts to Orin + peer\")\n"
            "```\n"
            "Then `/update` will always know what is happening."
        )

    # 3. Parse arguments (very permissive)
    watch = False
    show_all = False
    specific_id = None
    last_n = None

    if args:
        a = args.strip()
        a_lower = a.lower()

        if "watch" in a_lower:
            watch = True
        if a_lower == "all" or "--all" in a_lower:
            show_all = True
        elif a_lower.startswith("last "):
            try:
                last_n = int(a.split()[-1])
            except Exception:
                last_n = 8
        else:
            # Maybe a direct task id
            candidate = a.strip()
            if get_task(candidate):
                specific_id = candidate
            else:
                # last-ditch: any plausible id inside the arg string
                ids = extract_task_ids_only([a], limit=1)
                if ids and get_task(ids[0]):
                    specific_id = ids[0]

    # 4. Handle specific task detail view
    if specific_id:
        t = get_task(specific_id)
        poll = _poll(t) if t else None
        return format_detailed_task(t, poll)

    # 5. Select which tasks to show
    if last_n:
        selected = tasks[:last_n]
    elif show_all:
        selected = tasks
    else:
        # Default: running first, then recent failures, then a few completed
        running = [t for t in tasks if t.status == "running"]
        failed = [t for t in tasks if t.status == "failed"][:5]
        completed = [t for t in tasks if t.status == "completed"][:6]
        selected = running + failed + completed
        if not selected:
            selected = tasks[:14]

    # 6. Live poll everything we are about to display (this is the magic)
    for t in selected:
        if t.status == "running":
            res = _poll(t)
            if res:
                # tracker already updated via side effects in _poll
                if res.get("status") == "completed":
                    t.status = "completed"
                    t.exit_code = res.get("exit_code")
                if res.get("output"):
                    t.last_output = res["output"][-4000:]
                if res.get("error"):
                    t.error = res["error"]

    # 7. Beautiful output via the new formatter
    if watch:
        # Watch mode gives an excellent snapshot + tells the user how to keep watching
        body = format_everything(tasks, show_all=show_all)
        header = format_watch_header()
        return header + "\n\n" + body + "\n\n" + _watch_advice()

    # Normal excellent report
    body = format_everything(tasks, show_all=show_all)

    footer = []
    if newly_registered:
        footer.append(f"Auto-registered {newly_registered} previously forgotten task(s) from conversation history.")
    footer.append("Pro move: call `register_background_task(...)` immediately after every background launch.")
    if len(tasks) > len(selected):
        footer.append(f"Showing {len(selected)} of {len(tasks)}. Use `/update all` or `/update last 30`.")

    return body + "\n\n" + "\n".join(f"_{f}_" for f in footer)


def _watch_advice() -> str:
    return (
        "**Watch mode tips:**\n"
        "- Run `/update --watch` again any time you want a fresh snapshot\n"
        "- For true continuous watching: `/loop 30s /update`\n"
        "- Combine with monitors: `monitor tail -f /var/log/ion.log | grep --line-buffered bp` then `/update`"
    )


# Convenience re-exports so people can `from update import ...` easily
__all__ = [
    "handle_update",
    "register_background_task",
    "register_monitor",
]