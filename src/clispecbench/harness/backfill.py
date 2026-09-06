"""Evidence-based Codex telemetry migration; never reruns or rescores a model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from clispecbench.agents.codex_cli import (
    TOOL_CALLS_DEFINITION,
    CodexCLIAdapter,
    count_tool_calls,
)


def _read(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a result object: {path}")
    return cast(dict[str, Any], data)


def backfill_telemetry(
    runs_root: Path, published_root: Path | None = None, *, apply: bool = False
) -> list[dict[str, Any]]:
    """Preview or apply telemetry-only edits, matching publications by run_uid.

    Missing/ambiguous evidence is reported, never guessed. Raw JSON updates
    retain editorial fields, scores, costs, and original run metadata. The
    returned audit records old/new values; re-running is idempotent.
    """
    if not runs_root.is_dir():
        raise ValueError(f"Run directory does not exist: {runs_root}")
    originals: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    publications: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    audit: list[dict[str, Any]] = []
    for root, pattern, index in (
        (runs_root, "result.json", originals),
        (published_root, "run*.json", publications),
    ):
        if root is None:
            continue
        if not root.is_dir():
            raise ValueError(f"Result directory does not exist: {root}")
        for path in sorted(root.rglob(pattern)):
            try:
                data = _read(path)
                meta: dict[str, Any] = data.get("metadata") or {}
                if meta.get("agent") != "codex-cli":
                    continue
                uid = meta.get("run_uid")
                if not isinstance(uid, str) or not uid:
                    raise ValueError("Missing run_uid")
                index.setdefault(uid, []).append((path, data))
            except (OSError, ValueError, AttributeError) as exc:
                audit.append({"path": str(path), "status": "skipped", "reason": str(exc)})

    for uid in sorted(originals.keys() | publications.keys()):
        sources = originals.get(uid, [])
        targets = publications.get(uid, [])
        entry: dict[str, Any] = {"run_uid": uid, "status": "skipped"}
        if len(sources) != 1 or len(targets) > 1:
            entry["reason"] = "missing original run" if not sources else "ambiguous run_uid"
            audit.append(entry)
            continue
        path, data = sources[0]
        entry["source"] = str(path)
        try:
            texts: list[str] = []
            artifacts: dict[str, Any] = data.get("artifacts") or {}
            transcript = artifacts.get("transcript") or "transcript.jsonl"
            if not isinstance(transcript, str):
                raise ValueError("Transcript path is not a string")
            for name in dict.fromkeys([transcript, "codex-events.jsonl"]):
                candidate = (path.parent / name).resolve()
                if not candidate.is_relative_to(path.parent.resolve()):
                    raise ValueError("Transcript path leaves the run directory")
                if candidate.is_file():
                    texts.append(candidate.read_text(encoding="utf-8"))
            calls = count_tool_calls(texts)
            if calls is None:
                raise ValueError("Missing or unsupported Codex event transcript")
            usage = data.get("token_usage")
            if not isinstance(usage, dict):
                raise ValueError("No stored token_usage object; retain original unknown usage")
            usage = cast(dict[str, Any], usage)
            updates: dict[str, Any] = {
                "tool_calls": calls,
                "tool_calls_definition": TOOL_CALLS_DEFINITION,
            }
            parsed = CodexCLIAdapter().parse_token_usage(path.parent, texts[0] if texts else "")
            if parsed is not None and (
                parsed.input_tokens == usage.get("input_tokens")
                and parsed.output_tokens == usage.get("output_tokens")
            ):
                for name in (
                    "reasoning_output_tokens",
                    "cache_read_input_tokens",
                    "cache_creation_input_tokens",
                ):
                    value = getattr(parsed, name)
                    if value is not None:
                        # Do not introduce newly recovered nonzero cache usage
                        # without a separate cost reconciliation.
                        if name.startswith("cache_") and usage.get(name) != value:
                            if usage.get(name) is not None or value != 0:
                                continue
                        updates[name] = value

            changes: list[dict[str, Any]] = []
            for target, payload in [sources[0], *targets]:
                for key in ("task", "agent", "model", "timestamp"):
                    if payload["metadata"].get(key) != data["metadata"].get(key):
                        raise ValueError(f"run_uid metadata mismatch: {target}")
                target_usage = payload.get("token_usage")
                if not isinstance(target_usage, dict):
                    raise ValueError(f"Missing token_usage: {target}")
                target_usage = cast(dict[str, Any], target_usage)
                for key in ("input_tokens", "output_tokens"):
                    if target_usage.get(key) != usage.get(key):
                        raise ValueError(f"run_uid usage mismatch: {target}")
                changed = {k: v for k, v in updates.items() if target_usage.get(k) != v}
                if changed:
                    changes.append(
                        {
                            "path": str(target),
                            "old": {k: target_usage.get(k) for k in changed},
                            "new": changed,
                        }
                    )
            entry["changes"] = changes
            entry["status"] = (
                "updated" if apply and changes else "would_update" if changes else "unchanged"
            )
            if apply:
                for change in changes:
                    target = Path(change["path"])
                    payload = _read(target)
                    payload["token_usage"].update(change["new"])
                    temporary = target.with_suffix(".json.telemetry-tmp")
                    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                    temporary.replace(target)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            entry["reason"] = str(exc)
            entry["status"] = "skipped"
        audit.append(entry)
    return audit
