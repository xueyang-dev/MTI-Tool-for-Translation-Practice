"""Crash-safe batch checkpoints and translation-memory reconciliation."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple


EVENTS_FILE = "events.jsonl"


def events_path(job_root: Path) -> Path:
    return Path(job_root) / EVENTS_FILE


def append_event(job_root: Path, event: Dict[str, Any]) -> None:
    """Append one durable, JSON-serializable workflow event."""
    path = events_path(job_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_events(job_root: Path) -> List[Dict[str, Any]]:
    path = events_path(job_root)
    if not path.is_file():
        return []
    events = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                value = json.loads(line)
            except (TypeError, ValueError):
                continue
            if isinstance(value, dict):
                events.append(value)
    except OSError:
        return []
    return events


def _eligible(source: str, target: str) -> bool:
    return bool(str(source or "").strip()) and bool(str(target or "").strip())


def _state_entries(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    entries = {}
    for pair in state.get("pairs") or []:
        if not pair.get("reviewed") or pair.get("stale_due_to_glossary"):
            continue
        source, target = pair.get("source"), pair.get("target")
        if _eligible(source, target):
            entries[str(source)] = {"target": str(target), "reviewed": True}
    return entries


def reconcile_translation_memory(
    tm: Dict[str, Dict[str, Any]],
    state: Dict[str, Any],
    job_root: Path,
) -> Tuple[bool, int]:
    """Recover accepted state entries and pending TM promotions after restart."""
    desired = _state_entries(state)
    pending = 0
    events = read_events(job_root)
    promoted_batches = {event.get("batch") for event in events
                        if event.get("phase") in {"tm_promoted", "tm_promotion_done"}}
    for event in events:
        if event.get("phase") != "tm_promotion_pending":
            continue
        if event.get("batch") in promoted_batches:
            continue
        pending += 1
        for item in event.get("entries") or []:
            source, target = item.get("source"), item.get("target")
            if _eligible(source, target):
                desired[str(source)] = {"target": str(target), "reviewed": True}
    changed = False
    for source, entry in desired.items():
        if tm.get(source) != entry:
            tm[source] = entry
            changed = True
    return changed, pending


def batch_entries(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"source": str(pair.get("source") or ""),
         "target": str(pair.get("target") or "")}
        for pair in pairs
        if pair.get("reviewed") and not pair.get("stale_due_to_glossary")
        and _eligible(pair.get("source"), pair.get("target"))
    ]
