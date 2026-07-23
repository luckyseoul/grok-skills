---
name: update
description: Nuclear-grade background task tracker. Use for /update, status on anything launched with background:true, monitors, subagents, long ION/DTN operations, remote Orin work, or when the user says "any progress?", "how's it going?", "status", "what's running?". Auto-discovers forgotten tasks and produces gorgeous live reports.
---

# /update — Background Task Status (Turned Up to 11)

The single most important power tool when you run serious long-lived work (ION BPv7 nodes, DTN contact plans, remote Orin flashing, big compiles, log monitors, Hypothesis test batteries, etc.).

## The Only Commands You Actually Need

| Command                    | Effect |
|----------------------------|--------|
| `/update`                  | Best possible summary: running first, then failures, then recent completions. Auto-discovers anything it can. |
| `/update all`              | Every single tracked task (no truncation). |
| `/update last 12`          | The 12 most recent tasks. |
| `/update <task_id>`        | Full live card for one specific task (recommended for deep debugging). |
| `/update --watch`          | Beautiful snapshot + instructions for continuous watching. |

## Golden Rules (Follow These or Suffer)

**Rule 1 — Register immediately**

After every background launch:

```python
task_id = run_terminal_command(
    command="ionstart -I /home/nick/ion-config/host268485122.rc",
    background=True
)

from update import register_background_task
register_background_task(
    task_id=task_id,
    description="ION node 268485122 (soulkiller) with full bidirectional contacts to Orin + peer",
    command="ionstart -I /home/nick/ion-config/host268485122.rc",
    task_type="terminal"
)
```

**Rule 2 — Monitors too**

```python
mon_id = monitor(
    command='tail -f /var/log/ion.log | grep --line-buffered -E "(ERROR|bpclm|bundle)"',
    description="Live ION log watcher for bundle flow between 268485122 and 268485121",
    persistent=True
)

from update import register_monitor
register_monitor(
    monitor_id=mon_id,
    description="ION log tail - bundle + error events",
    command="tail -f ..."
)
```

**Rule 3 — Just type `/update`**

Whenever the human says:
- "any progress?"
- "status"
- "how's the node?"
- "update"
- "what's running?"
- "is the Orin link up?"

Your response should start with calling the `update` skill (i.e. produce `/update` or directly invoke `handle_update`).

## What Makes This Version Nuclear

- **Conversation archaeology**: Even if you completely forget to register, it rips through recent assistant messages + tool results and auto-registers task_ids it finds (with decent descriptions).
- **Live polling on every call**: Calls `get_command_or_subagent_output` on everything it shows so you always see current stdout/exit state.
- **Beautiful output**: Color-aware (when the TUI supports it), smart excerpts that don't drown you in ION noise, proper durations, status that actually means something.
- **Watch mode + `/loop` synergy**: `/update --watch` + `/loop 30s /update` gives you near-real-time observability without manual effort.
- **Subagent + monitor awareness**: Knows the difference between a terminal background command, a `monitor` stream, and a spawned subagent.

## Real-World DTN / ION Example

```python
# 1. Bring up soulkiller node
tid = run_terminal_command(
    command="bash /home/nick/ion-config/start-soulkiller.sh",
    background=True,
    timeout=120000
)
register_background_task(tid, "ION BPv7 node 268485122 full startup + contact plan", task_type="terminal")

# 2. Start a receiver on the other side (via ssh to Orin)
rid = run_terminal_command("sshpass -p drpepper ssh nick@100.70.177.14 'bpsink ipn:268485121.1 > /tmp/bundles.log &'", background=True)
register_background_task(rid, "Remote bpsink on Orin (268485121.1) logging bundles", task_type="terminal")

# 3. Fire a monitor for the log
mid = monitor("tail -f /home/nick/ion.log | grep --line-buffered -E 'bpclm|bundle|ERROR'", description="ION bundle events on soulkiller")
register_monitor(mid, "Live bundle flow monitor - soulkiller")

# Later, any time:
# /update
# /update last 8
# /update <that tid from step 1>
```

## Output Quality (What You Actually See)

Running tasks are shown first with live tail excerpts.

Failures are highlighted in red and never buried.

Completed tasks show exit codes cleanly.

Every line has age, type icon, and the single most recent interesting output line.

For one specific task (`/update <id>`) you get the full recent output buffer + metadata.

## Watch Mode

`/update --watch` produces a timestamped report and tells you the best ways to keep watching:

- Just run `/update --watch` again manually when you feel like it
- Real continuous mode: `/loop 20s /update`
- Combine with a real `monitor` for the actual log stream

## Advanced / Power User Moves

- `from update import scan_for_tasks` — manually trigger the archaeology engine on any text blob.
- `from update import smart_excerpt` — use the same log-trimming logic the skill uses.
- After killing a task with `kill_command_or_subagent`, call `mark_task_failed(task_id, "killed by user")` so `/update` shows the truth.
- The skill keeps its own `~/.grok/skills/update/tasks.json` (last 60 tasks). You can cat it when debugging the skill itself.

## Why This Skill Exists

Because the platform gives you `task_id`s and then the conversation moves on. 45 minutes later you have no idea which of the 9 background things you started is the one that is still building the contact graph or the one that crashed the SDR.

`/update` ends that pain permanently.

This is the maximum-power version. Use it on every serious session.