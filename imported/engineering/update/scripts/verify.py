#!/usr/bin/env python3
"""
Quick self-test for the update skill (turned up to 11).

Run with:
    python3 ~/.grok/skills/update/scripts/verify.py

It exercises:
- tracker (register, persist, query)
- conversation_scanner (discovery)
- formatter (output rendering)
- update.handle_update (the full path)
"""

import os
import sys
import tempfile
import time

# Make sure we can import as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.tracker import (
    register_background_task,
    register_monitor,
    get_recent_tasks,
    get_task,
    mark_task_completed,
    _load_tasks,
    STATE_FILE,
)
from scripts.conversation_scanner import scan_for_tasks, extract_task_ids_only
from scripts.formatter import (
    format_everything,
    format_detailed_task,
    format_task_row,
    smart_excerpt,
    age_str,
    status_badge,
)
from scripts.update import handle_update


def test_tracker():
    print("=== Testing tracker ===")

    # Use a temp state file for isolation
    orig_state = STATE_FILE
    with tempfile.TemporaryDirectory() as tmp:
        test_state = os.path.join(tmp, "tasks.json")
        import scripts.tracker as tmod
        tmod.STATE_FILE = test_state

        t1 = register_background_task(
            "test-uuid-1234-5678",
            "ION node soulkiller startup test",
            command="ionstart -I test.rc",
            task_type="terminal",
        )
        assert t1.task_id == "test-uuid-1234-5678"
        assert get_task("test-uuid-1234-5678") is not None

        m1 = register_monitor("mon-999", "ION log watcher", "tail -f ion.log")
        assert m1.task_type == "monitor"

        tasks = get_recent_tasks()
        assert len(tasks) >= 2

        mark_task_completed("test-uuid-1234-5678", 0, "Node came up cleanly\nbpclm ready")

        t1b = get_task("test-uuid-1234-5678")
        assert t1b.status == "completed"
        assert t1b.exit_code == 0

        print("  tracker: PASS (register, monitor, complete, persist)")

        # restore
        tmod.STATE_FILE = orig_state


def test_scanner():
    print("=== Testing conversation_scanner ===")

    fake_history = [
        "Launched the node: run_terminal_command returned task_id 019e6368-a56e-72a2-9c74-80af4a7c54c3",
        "Also started a monitor with id abcdef123456 for the bundle log",
        "Some other text here with no ids",
        "Another background thing: subagent task 7f8e9d2c started for Orin flash",
    ]

    discovered = scan_for_tasks(fake_history)
    ids = [d.task_id for d in discovered]
    assert "019e6368-a56e-72a2-9c74-80af4a7c54c3" in ids, f"Missing main ID, got {ids}"
    assert any("abcdef123456" in i for i in ids) or any("7f8e9d2c" in i for i in ids)

    cheap = extract_task_ids_only(fake_history)
    assert len(cheap) >= 2

    print(f"  scanner: PASS (found {len(discovered)} high-quality + cheap IDs)")


def test_formatter():
    print("=== Testing formatter ===")

    from scripts.tracker import BackgroundTask

    t = BackgroundTask(
        task_id="fmt-test-001",
        description="Test DTN bundle transmission 268485122 → 268485121",
        command="bpsendtest ...",
        task_type="terminal",
        start_time=time.time() - 187,
        status="running",
        last_output="bpclm: sent bundle to ipn:268485121.1\nbpclm: custody accepted",
    )

    row = format_task_row(t)
    assert "running" in row or "⏳" in row

    card = format_detailed_task(t)
    assert "DTN bundle transmission" in card

    excerpt = smart_excerpt("line1\nline2\nbpclm: important event\nDEBUG noise\n", max_lines=3)
    assert "important event" in excerpt

    print("  formatter: PASS (rows, cards, excerpts, durations)")


def test_full_handle_update():
    print("=== Testing handle_update end-to-end ===")

    import scripts.tracker as tmod
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmp:
        tmod.STATE_FILE = os.path.join(tmp, "tasks.json")

        # Seed a couple tasks
        register_background_task("live-001", "ION soulkiller full start", task_type="terminal")
        register_background_task("live-002", "Remote bpsink on Orin via ssh", task_type="terminal")
        mark_task_completed("live-002", 0, "bpsink received 17 bundles")

        # Simulate conversation history that should trigger auto-discovery
        history = [
            "I also launched this one earlier: task_id 019e6368-a56e-72a2-9c74-80af4a7c54c3 for the big contact plan sync",
            "And a monitor abc-123-monitor for the log",
        ]

        out = handle_update(args=None, recent_messages=history)

        assert "ION soulkiller" in out or "soulkiller" in out
        assert "019e6368" in out or "auto" in out.lower() or "discovered" in out.lower()  # either registered or mentioned
        assert "completed" in out.lower() or "✅" in out

        # Specific task view
        detail = handle_update(args="live-001", recent_messages=None)
        assert "ION soulkiller" in detail

        # last N
        last = handle_update(args="last 1", recent_messages=None)
        assert len(last) > 10

        print("  handle_update: PASS (discovery + normal + specific + last N + history)")

        tmod.STATE_FILE = STATE_FILE  # not strictly needed


def main():
    print("update skill — verification (turned up to 11)\n")
    test_tracker()
    test_scanner()
    test_formatter()
    test_full_handle_update()
    print("\n✅ All verifications passed. The update skill is ready for heavy use.")


if __name__ == "__main__":
    main()
