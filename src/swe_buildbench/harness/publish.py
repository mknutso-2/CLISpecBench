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
from pathlib import Path

from swe_buildbench.harness.results import load_result

log = logging.getLogger(__name__)


class PublishError(Exception):
    """Raised when a result cannot be published."""


def published_runs_dir(
    published_root: Path,
    task: str,
    agent: str,
    model: str | None,
    effort: str | None,
) -> Path:
    """Return ``<published_root>/<task>/<agent>/<model-effort>/``."""
    base = published_root / task / agent
    if model:
        slug = f"{model}_{effort}" if effort else model
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


def find_duplicate_publication(published_root: Path, run_uid: str) -> Path | None:
    """Return the path of an already-published file carrying ``run_uid``, if any.

    Malformed publications are tolerated during the scan — a corrupt file can
    not vouch for its own uid, so we skip it and keep looking rather than
    either bypassing the check (silently) or crashing the publish (loudly).
    Readers interested in surfacing corruption can re-scan and report, but
    that is a separate concern from "is this uid already claimed".
    """
    if not run_uid or not published_root.is_dir():
        return None
    for p in published_root.rglob("run*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            existing_uid = data["metadata"]["run_uid"]
        except (OSError, json.JSONDecodeError):
            log.warning("Skipping unreadable published file during duplicate scan: %s", p)
            continue
        except (KeyError, TypeError):
            # Wrong shape (not a dict, missing keys, null metadata, etc.).
            # Can't vouch for a uid we can't read — skip and keep looking.
            continue
        if existing_uid == run_uid:
            return p
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
            f"{source}: result has no run_uid (pre-2.0 file). "
            "Re-run the evaluation to produce a publishable result."
        )

    existing = find_duplicate_publication(published_root, meta.run_uid)
    if existing and not force:
        raise PublishError(
            f"run_uid {meta.run_uid} already published at "
            f"{existing.relative_to(published_root.parent)}. Use --force to overwrite."
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
        existing if (existing and force)
        else target_dir / f"run{next_published_run_number(target_dir)}.json"
    )

    payload = result.to_dict()
    # Artifacts live alongside the transient result; the path is meaningless
    # once published. Cross-reference via metadata.run_uid.
    payload.pop("artifacts", None)
    payload["editorial"] = {
        "status": status,
        "last_message": last_message,
        "commentary": commentary,
    }

    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.info("Published %s -> %s", source, target_path)
    return target_path
