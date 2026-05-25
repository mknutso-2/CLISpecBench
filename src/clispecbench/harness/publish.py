"""Publish a transient run result into the curated published_results/ tree.

Transient results live in a gitignored scratch dir. A run is "published" by
copying its structural data (scores, token usage, per-test outcomes) into
``published_results/<task>/<agent>/<model-effort>/runN.json`` alongside
editorial fields a human (or AI) sign-off provides. The ``metadata.run_uid``
is the stable cross-reference handle back to the original transient copy.

The publish action is intentionally a single-file write so each publication is
one reviewable change in git. Revert the commit to un-publish.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

from clispecbench.harness.results import RunResult, load_result, model_effort_slug
from clispecbench.harness.status import (
    DEPRECATED_STATUS_REPLACEMENTS,
    STATUS_TO_EXIT_CLASS,
    VALID_STATUSES,
)

log = logging.getLogger(__name__)


class PublishError(Exception):
    """Raised when a result cannot be published."""


UNPUBLISHABLE_STOP_REASON_LABELS = {
    "usage_limit": "account/usage limit",
    "stream_disconnect": "local/network stream disconnect",
    "auth_failure": "authentication failure",
}


def published_runs_dir(
    published_root: Path,
    task: str,
    agent: str,
    model: str | None,
    effort: str | None,
) -> Path:
    """Return ``<published_root>/<task>/<agent>/<model-effort>/``."""
    base = published_root / task / agent
    slug = model_effort_slug(model, effort)
    if slug:
        base = base / slug
    return base


def next_published_run_number(target_dir: Path) -> int:
    """Return ``N`` such that ``run<N>.json`` is the next free slot."""
    if not target_dir.is_dir():
        return 1
    existing: list[int] = []
    for p in target_dir.iterdir():
        if p.is_file() and p.name.startswith("run") and p.suffix == ".json":
            stem = p.stem[3:]
            if stem.isdigit():
                existing.append(int(stem))
    return max(existing, default=0) + 1


def find_duplicate_publications(published_root: Path, run_uid: str) -> list[Path]:
    """Return all published files carrying ``run_uid``.

    A healthy tree has at most one. Returning a list (not the first hit) lets
    ``publish_result`` enforce the at-most-one invariant and refuse to act on
    a tree where the same uid has been published more than once — that state
    is always a prior bug and silently overwriting one of the duplicates
    would just compound it.

    Malformed publications are tolerated during the scan — a corrupt file
    can't vouch for its uid, so we skip it and keep looking rather than
    either bypassing the check (silently) or crashing the publish (loudly).
    """
    if not run_uid or not published_root.is_dir():
        return []
    matches: list[Path] = []
    for p in sorted(published_root.rglob("run*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            existing_uid = data["metadata"]["run_uid"]
        except (OSError, json.JSONDecodeError):
            log.warning("Skipping unreadable published file during duplicate scan: %s", p)
            continue
        except (KeyError, TypeError):
            # Wrong shape (not a dict, missing keys, null metadata, etc.).
            continue
        if existing_uid == run_uid:
            matches.append(p)
    return matches


def find_duplicate_publication(published_root: Path, run_uid: str) -> Path | None:
    """Return the first published file carrying ``run_uid``, or ``None``.

    Thin wrapper around :func:`find_duplicate_publications` preserved for
    callers that only need the existence check.
    """
    matches = find_duplicate_publications(published_root, run_uid)
    return matches[0] if matches else None


def _find_commentary_file(published_root: Path, slug: str) -> Path | None:
    """Return the first ``commentary/<slug>.md`` found under published_root."""
    if not slug or not published_root.is_dir():
        return None
    for p in published_root.glob(f"*/commentary/{slug}.md"):
        return p
    return None


def _classify_unpublishable_stop_message(message: str) -> str | None:
    text = message.strip().lower()
    if not text:
        return None
    if "usage limit" in text or "you've hit your limit" in text or "usage cap" in text:
        return "usage_limit"
    if (
        "stream disconnected" in text
        or "idle timeout" in text
        or "websocket" in text
        or "connection reset" in text
        or "connectionrefused" in text.replace(" ", "")
        or "unable to connect to api" in text
        or "network is unreachable" in text
    ):
        return "stream_disconnect"
    # Substring "401"/"403" matches dates like "20240122" inside agent prose
    # (e.g. an RRULE example). Require word boundaries so the match means an
    # HTTP status code, not arbitrary digit runs.
    if (
        re.search(r"\b401\b", text)
        or re.search(r"\b403\b", text)
        or "unauthorized" in text
        or "invalid api key" in text
        or "expired credential" in text
        or "missing api key" in text
    ):
        return "auth_failure"
    return None


def _iter_jsonl_dicts(path: Path) -> Iterator[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield cast(dict[str, Any], event)


def _final_codex_turn_failure_message(source: Path) -> str | None:
    event_log = source.parent / "codex-events.jsonl"
    if not event_log.is_file():
        return None

    final_turn: dict[str, Any] | None = None
    for event in _iter_jsonl_dicts(event_log):
        if event.get("type") in {"turn.completed", "turn.failed"}:
            final_turn = event

    if not final_turn or final_turn.get("type") != "turn.failed":
        return None

    raw_error: Any = final_turn.get("error")
    if isinstance(raw_error, dict):
        error = cast(dict[str, Any], raw_error)
        message = error.get("message")
        return message if isinstance(message, str) else None
    return raw_error if isinstance(raw_error, str) else None


def _unpublishable_stop_reason(
    source: Path,
    result: RunResult,
    status: str,
    last_message: str,
) -> str | None:
    if result.metadata.agent == "codex-cli":
        reason = _classify_unpublishable_stop_message(
            _final_codex_turn_failure_message(source) or ""
        )
        if reason:
            return reason

    candidates = [
        result.metadata.agent_last_message or "",
        result.metadata.notes or "",
        status,
        last_message,
    ]
    for candidate in candidates:
        reason = _classify_unpublishable_stop_message(candidate)
        if reason:
            return reason
    return None


def publish_result(
    source: Path,
    published_root: Path,
    *,
    status: str,
    last_message: str,
    commentary: str | None = None,
    force: bool = False,
) -> Path:
    """Publish one transient ``result.json`` into ``published_root``.

    Returns the path of the newly written published file.
    """
    result = load_result(source)
    meta = result.metadata

    if not meta.run_uid:
        raise PublishError(
            f"{source}: result has no run_uid. "
            "Re-run the evaluation to produce a publishable result."
        )

    # Validate the editorial --status against the canonical taxonomy. Reject
    # typos, deprecated labels, and freeform strings outright — the dashboard
    # inclusion gate keys off this string and a typo silently demotes a real
    # result into the Excluded bucket. See clispecbench.harness.status.
    if status not in VALID_STATUSES:
        if status in DEPRECATED_STATUS_REPLACEMENTS:
            replacement = DEPRECATED_STATUS_REPLACEMENTS[status]
            raise PublishError(
                f"{source}: status {status!r} is deprecated. "
                f"Re-classify the run and pass --status {replacement!r} instead "
                f"(see clispecbench.harness.status.DEPRECATED_STATUS_REPLACEMENTS "
                f"for the migration mapping)."
            )
        valid = ", ".join(sorted(VALID_STATUSES))
        raise PublishError(
            f"{source}: status {status!r} is not a recognized editorial label. "
            f"Pass one of: {valid}. See .claude/skills/run-eval/SKILL.md for the "
            "bucket definitions and clispecbench.harness.status for the canonical list."
        )

    stop_reason = _unpublishable_stop_reason(source, result, status, last_message)
    if stop_reason:
        label = UNPUBLISHABLE_STOP_REASON_LABELS[stop_reason]
        raise PublishError(
            f"{source}: not publishable because the run stopped due to {label}, "
            "which is a user/environment failure rather than model or harness behavior."
        )

    existing_matches = find_duplicate_publications(published_root, meta.run_uid)
    if len(existing_matches) > 1:
        paths = "\n  ".join(str(p) for p in existing_matches)
        raise PublishError(
            f"run_uid {meta.run_uid} already appears in more than one published "
            f"file — the at-most-one invariant is broken. Resolve manually before "
            f"publishing:\n  {paths}"
        )

    existing = existing_matches[0] if existing_matches else None
    if existing and not force:
        raise PublishError(
            f"run_uid {meta.run_uid} already published at "
            f"{existing.relative_to(published_root.parent)}. Use --force to overwrite."
        )

    if commentary and _find_commentary_file(published_root, commentary) is None:
        log.warning(
            "commentary slug %r has no matching file under %s/*/commentary/ "
            "— publishing anyway (verify the file lands in the same change)",
            commentary,
            published_root.name,
        )

    target_dir = published_runs_dir(
        published_root,
        meta.task,
        meta.agent,
        meta.model,
        meta.effort,
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = (
        existing
        if (existing and force)
        else target_dir / f"run{next_published_run_number(target_dir)}.json"
    )

    payload = result.to_dict()
    # Artifacts live alongside the transient result; the path is meaningless
    # once published. Cross-reference via metadata.run_uid.
    payload.pop("artifacts", None)
    # Auto-populate metadata.exit_class from --status. This is the canonical
    # field the rest of the harness reads to classify a run; the editorial
    # status is for humans and the dashboard. Keeping them derived from the
    # same source means a typo in --status would have been rejected above
    # before reaching this point, so the two can't drift.
    metadata = payload.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        payload["metadata"] = metadata
    metadata["exit_class"] = STATUS_TO_EXIT_CLASS[status]
    payload["editorial"] = {
        "status": status,
        "last_message": last_message,
        "commentary": commentary,
    }

    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.info("Published %s -> %s", source, target_path)
    return target_path
