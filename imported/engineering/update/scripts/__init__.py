"""
update skill - Nuclear background task observability ("turned up to 11").

The one command you actually use when you have 14 background ION nodes,
monitors, compiles, and remote Orin operations running at once.

Public API (use these):
    from update import (
        register_background_task,
        register_monitor,
        handle_update,          # called by the TUI for /update
        get_recent_tasks,
        get_task,
    )

Also available for advanced use:
    - conversation_scanner.scan_for_tasks
    - formatter.* (beautiful text rendering)
"""

from .tracker import (
    register_background_task,
    register_monitor,
    get_recent_tasks,
    get_task,
    get_active_tasks,
    mark_task_completed,
    mark_task_failed,
    update_task_output,
)
from .update import handle_update
from .conversation_scanner import scan_for_tasks, extract_task_ids_only
from .formatter import (
    format_everything,
    format_detailed_task,
    format_table,
    smart_excerpt,
    age_str,
)

__all__ = [
    # Primary things you call after launching work
    "register_background_task",
    "register_monitor",
    # The /update command implementation
    "handle_update",
    # Inspection
    "get_recent_tasks",
    "get_task",
    "get_active_tasks",
    # Advanced / power features
    "scan_for_tasks",
    "extract_task_ids_only",
    "format_everything",
    "format_detailed_task",
    "format_table",
    "smart_excerpt",
    "age_str",
    # Manual status sync (rarely needed)
    "mark_task_completed",
    "mark_task_failed",
    "update_task_output",
]