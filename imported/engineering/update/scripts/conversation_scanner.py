"""
conversation_scanner.py - Aggressive auto-discovery of background tasks.

Scans recent conversation history (assistant messages, tool results, raw text)
for task_ids that were never explicitly registered via register_background_task.

This is the fallback that makes the skill "just work" even when the model forgets
to call register_background_task after launching something with background=True.
"""

import re
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple


# Matches standard UUIDs and the short alphanumeric task IDs the platform uses
TASK_ID_RE = re.compile(
    r'\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[a-z0-9]{7,20})\b',
    re.IGNORECASE
)

# Common patterns where task_ids appear right after launch
LAUNCH_PATTERNS = [
    re.compile(r'task_id["\s:=]+([0-9a-f]{8}-[0-9a-f-]{20,})', re.I),
    re.compile(r'task_id["\s:=]+([a-z0-9]{7,20})', re.I),
    re.compile(r'"task_id"\s*:\s*"([^"]+)"', re.I),
    re.compile(r'background.*task_id[:\s]+([^\s,]+)', re.I),
    re.compile(r'Launched.*task_id[:\s]+([^\s]+)', re.I),
    re.compile(r'started.*background.*(?:id|task)[:\s]+([a-z0-9-]+)', re.I),
]

# Patterns that give us a human description near a task launch
DESC_NEAR_ID_RE = re.compile(
    r'(?:starting|launched|running|background|monitor|subagent)[^\n]{0,80}?(?:task|id)[:\s]+([a-z0-9-]{6,})[^\n]{0,120}',
    re.IGNORECASE
)

# Look for monitor tool usage
MONITOR_RE = re.compile(r'monitor.*command["\s:=]+([^\n"]+)', re.I)

# Look for subagent spawn
SUBAGENT_RE = re.compile(r'spawn_subagent|subagent.*task_id', re.I)


@dataclass
class DiscoveredTask:
    task_id: str
    description: str
    task_type: str = "terminal"  # terminal | monitor | subagent
    started_at: Optional[float] = None
    source_snippet: str = ""
    confidence: float = 0.5


def _looks_like_task_id(s: str) -> bool:
    if not s:
        return False
    s = s.strip()
    if len(s) < 6:
        return False
    # UUID shape
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}', s, re.I):
        return True
    # Short hex-ish or alphanum the platform tends to emit
    if re.match(r'^[a-z0-9]{7,20}$', s, re.I) and not s.isdigit():
        return True
    return False


def _extract_description_near(text: str, task_id: str, window: int = 220) -> str:
    """Try to find a meaningful description in the vicinity of a task_id mention."""
    idx = text.lower().find(task_id.lower())
    if idx == -1:
        return "Auto-discovered background task"

    start = max(0, idx - window)
    end = min(len(text), idx + len(task_id) + window)
    window_text = text[start:end]

    # Look for "description" or natural language launch phrases
    for pat in [
        r'description["\s:=]+["\']?([^"\'\n]{5,120})',
        r'(?:starting|launched|running|monitor|subagent)[^\n:]{0,40}[:\-]\s*([A-Za-z][^\n]{5,100})',
        r'Command:\s*`?([^`\n]{5,100})',
    ]:
        m = re.search(pat, window_text, re.IGNORECASE)
        if m:
            desc = m.group(1).strip().strip('`"\'')
            if len(desc) > 4:
                return desc[:140]

    # Fallback: take a sentence-like chunk around the id
    lines = window_text.splitlines()
    for line in lines:
        if task_id.lower() in line.lower():
            clean = re.sub(r'\s+', ' ', line).strip()[:160]
            if clean:
                return clean

    return "Auto-discovered background task"


def scan_for_tasks(
    recent_messages: List[str],
    max_tasks: int = 30,
    min_confidence: float = 0.35,
) -> List[DiscoveredTask]:
    """
    The main entry point.

    Takes raw recent conversation strings (assistant turns, tool results, etc.)
    and returns candidate BackgroundTask-like objects that should be registered.
    """
    if not recent_messages:
        return []

    # Join with markers so we can still reason about source
    full_text = "\n\n===MSG===\n\n".join(recent_messages[-120:])  # generous window

    discovered: Dict[str, DiscoveredTask] = {}

    # 1. Direct ID extraction (highest coverage)
    raw_ids = TASK_ID_RE.findall(full_text)
    for raw in raw_ids:
        tid = raw.strip()
        if not _looks_like_task_id(tid):
            continue
        if tid in discovered:
            continue

        desc = _extract_description_near(full_text, tid)
        task_type = "terminal"

        # Classify type from surrounding context
        lower_ctx = full_text.lower()
        if "monitor" in lower_ctx and tid in lower_ctx:
            # crude but effective
            idx = lower_ctx.find(tid.lower())
            ctx = lower_ctx[max(0, idx-80):idx+80]
            if "monitor" in ctx:
                task_type = "monitor"
        if SUBAGENT_RE.search(full_text[max(0, full_text.lower().find(tid.lower())-120):]):
            task_type = "subagent"

        discovered[tid] = DiscoveredTask(
            task_id=tid,
            description=desc,
            task_type=task_type,
            source_snippet=full_text[max(0, full_text.lower().find(tid.lower())-40):full_text.lower().find(tid.lower())+80][:200],
            confidence=0.65,
        )

    # 2. Stronger launch pattern matches (higher confidence)
    for pat in LAUNCH_PATTERNS:
        for m in pat.finditer(full_text):
            tid = m.group(1).strip()
            if not _looks_like_task_id(tid):
                continue
            if tid not in discovered:
                desc = _extract_description_near(full_text, tid)
                discovered[tid] = DiscoveredTask(
                    task_id=tid,
                    description=desc,
                    task_type="terminal",
                    confidence=0.8,
                )
            else:
                discovered[tid].confidence = max(discovered[tid].confidence, 0.8)

    # 3. Explicit monitor commands
    for m in MONITOR_RE.finditer(full_text):
        cmd = m.group(1)[:120]
        # Try to pair with a nearby ID
        nearby = full_text[max(0, m.start()-200):m.end()+200]
        ids = TASK_ID_RE.findall(nearby)
        for tid in ids:
            if _looks_like_task_id(tid) and tid in discovered:
                discovered[tid].task_type = "monitor"
                discovered[tid].description = f"Monitor: {cmd}"
                discovered[tid].confidence = max(discovered[tid].confidence, 0.9)

    # Filter + sort by confidence + recency (later in text = more recent)
    results = [d for d in discovered.values() if d.confidence >= min_confidence]
    # Simple heuristic: longer source snippets and higher confidence first
    results.sort(key=lambda d: (d.confidence, len(d.source_snippet)), reverse=True)
    return results[:max_tasks]


def extract_task_ids_only(texts: List[str], limit: int = 50) -> List[str]:
    """Lightweight version used by the older update.py path."""
    if not texts:
        return []
    blob = "\n".join(texts)
    matches = TASK_ID_RE.findall(blob)
    seen = set()
    out = []
    for m in matches:
        if m not in seen and _looks_like_task_id(m):
            seen.add(m)
            out.append(m)
        if len(out) >= limit:
            break
    return out


def build_description_from_context(task_id: str, context: str) -> str:
    """Public helper for when you have a single ID and surrounding text."""
    return _extract_description_near(context, task_id)
