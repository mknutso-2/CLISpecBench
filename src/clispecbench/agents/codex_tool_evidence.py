"""Read session outputs for explicit nested pre-item process rejections.

This collects evidence; it does not infer corrected tool counts. Generated
code is never executed and submitted source is never imported.
"""

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast


def records(path: Path, *, strict: bool = False) -> Iterator[tuple[int, dict[str, Any]]]:
    for number, line in enumerate(path.read_text().splitlines(), 1):
        try:
            value = json.loads(line)
        except (json.JSONDecodeError, UnicodeError):
            if strict and line.strip():
                raise ValueError(f"Malformed session record at line {number}") from None
            continue
        if isinstance(value, dict):
            yield number, value


def failed_wrapper_blocks(payload: dict[str, Any]) -> list[str]:
    """Require the runtime failure envelope, never arbitrary printed stdout."""
    output = payload.get("output")
    if not isinstance(output, list) or not output or not isinstance(output[0], dict):
        return []
    output = cast(list[Any], output)
    envelope = cast(dict[str, Any], output[0]).get("text", "")
    if (
        not isinstance(envelope, str)
        or not envelope.startswith("Script failed\nWall time ")
        or "\nOutput:" not in envelope
    ):
        return []
    return [
        cast(dict[str, Any], block).get("text", "")
        for block in output[1:]
        if isinstance(block, dict) and isinstance(cast(dict[str, Any], block).get("text"), str)
    ]


def explicit_pre_item_rejection(payload: dict[str, Any]) -> list[str]:
    return [
        text
        for text in failed_wrapper_blocks(payload)
        if text.startswith("Script error:\nexec_command failed: CreateProcess")
        and "Rejected(" in text
    ]


def scan(session_root: Path, events_path: Path) -> dict[str, Any]:
    requests: dict[str | None, list[dict[str, Any]]] = {}
    outputs: list[dict[str, Any]] = []
    other_outputs: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    items: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    paths = sorted(session_root.rglob("*.jsonl"))
    for path in paths:
        try:
            manifest.append(
                {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            )
            session_records = list(records(path, strict=True))
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append(f"Unreadable or incomplete session: {path}: {exc}")
            continue
        for line, event in session_records:
            value = event.get("payload", {})
            if event.get("type") != "response_item" or not isinstance(value, dict):
                continue
            value = cast(dict[str, Any], value)
            typ = value.get("type")
            call_id = value.get("call_id")
            context = {"path": str(path), "line": line, "payload": value}
            if typ in {
                "custom_tool_call", "function_call",
                "custom_tool_call_output", "function_call_output",
            } and (not isinstance(call_id, str) or not call_id):
                errors.append(f"Invalid tool call ID at {path}:{line}")
                continue
            if typ in {"custom_tool_call", "function_call"}:
                requests.setdefault(call_id, []).append(context)
            elif typ in {"custom_tool_call_output", "function_call_output"}:
                if explicit_pre_item_rejection(value):
                    outputs.append(context)
                elif failed_wrapper_blocks(value):
                    other_outputs.append(context)
    if events_path.is_file():
        manifest.append(
            {
                "path": str(events_path),
                "sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
            }
        )
        for line, event in records(events_path):
            item = event.get("item", {})
            if event.get("type") not in {
                "item.started",
                "item.updated",
                "item.completed",
            } or not isinstance(item, dict):
                continue
            item = cast(dict[str, Any], item)
            if item.get("type") in {
                "command_execution",
                "file_change",
                "mcp_tool_call",
                "web_search",
            }:
                ident = item.get("id")
                if not isinstance(ident, str) or not ident:
                    errors.append(f"Invalid canonical item ID at {events_path}:{line}")
                    continue
                items[ident] = {
                    "line": line,
                    "id": ident,
                    "type": item.get("type"),
                    "command": item.get("command"),
                    "status": item.get("status"),
                    "exit_code": item.get("exit_code"),
                }
    failures: list[dict[str, Any]] = []
    seen: set[str | None] = set()
    for output in outputs:
        call_id = output["payload"].get("call_id")
        if call_id in seen:
            continue
        seen.add(call_id)
        failures.append(
            {
                "call_id": call_id,
                "requests": requests.get(call_id, []),
                "rejection_output": output,
                "rejection_outputs": [o for o in outputs if o["payload"].get("call_id") == call_id],
            }
        )
    return {
        "schema_version": 1,
        "evidence_errors": errors,
        "scope": "Explicit nested process rejection evidence; no inferred corrected count.",
        "other_failed_wrappers": [
            {
                "call_id": output["payload"].get("call_id"),
                "requests": requests.get(output["payload"].get("call_id"), []),
                "output": output,
            }
            for output in other_outputs
        ],
        "session_files": len(paths),
        "canonical_events_present": events_path.is_file(),
        "rejection_count": len(failures),
        "rejections": failures,
        "canonical_items": list(items.values()),
        "evidence_manifest": manifest,
    }
