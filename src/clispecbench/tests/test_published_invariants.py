"""Invariant tests for the published_results/ tree.

Per .claude/skills/run-eval/SKILL.md, every file under ``published_results/``
must satisfy one of:

  * ``metadata.exit_reason == "completed"`` — the agent self-terminated; the
    score reflects what the agent actually built and is included in
    Best/Mean calculations.
  * ``editorial.status`` is one of the ``model_*`` labels in
    :data:`clispecbench.harness.status.INCLUDED_NON_COMPLETED_STATUSES` —
    the agent exited via something other than its own completion path
    (timeout, output-token cap, build failure, etc.) but the score is still
    informative model signal.

Anything outside that is ``infra_*`` (auth failure, account/usage cap, host
or network drop) and per policy must never appear in published_results. The
publish CLI gate (``clispecbench.harness.publish``) catches these at
publish-time, but pre-policy data, manual edits, or future gate bugs could
still slip through — these tests are the belt-and-suspenders that fail CI
if the tree drifts off-policy.
"""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clispecbench.harness.status import INCLUDED_NON_COMPLETED_STATUSES

REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLISHED_ROOT = REPO_ROOT / "published_results"


def _published_run_files() -> list[Path]:
    """Every published ``run*.json`` outside the dashboard ``web/`` build dir."""
    if not PUBLISHED_ROOT.is_dir():
        return []
    return [
        p
        for p in sorted(PUBLISHED_ROOT.rglob("run*.json"))
        if "web" not in p.relative_to(PUBLISHED_ROOT).parts
    ]


def _row_id(path: Path) -> str:
    return str(path.relative_to(PUBLISHED_ROOT))


def test_every_published_run_is_completed_or_model_failure() -> None:
    """Each published run must qualify for dashboard inclusion.

    A run qualifies iff its ``metadata.exit_reason`` is ``"completed"`` OR
    its ``editorial.status`` is in the canonical
    :data:`INCLUDED_NON_COMPLETED_STATUSES` set. Any run that fails this
    check is an off-policy publication — most likely a legacy file from
    before the strict publish gate, but possibly a manual edit or a hole
    in the gate. Failing here surfaces it loudly instead of letting it
    silently corrupt the dashboard.
    """
    files = _published_run_files()
    assert files, f"no run*.json found under {PUBLISHED_ROOT} — repo layout regression?"

    violations: list[str] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append(f"{_row_id(path)}: malformed JSON ({exc})")
            continue
        metadata = payload.get("metadata") or {}
        editorial = payload.get("editorial") or {}
        exit_reason = metadata.get("exit_reason") or ""
        status = editorial.get("status") or ""
        if exit_reason == "completed":
            continue
        if status in INCLUDED_NON_COMPLETED_STATUSES:
            continue
        violations.append(
            f"{_row_id(path)}: exit_reason={exit_reason!r}, "
            f"editorial.status={status!r} — neither completed nor a recognized model_* bucket"
        )

    if violations:
        listing = "\n  ".join(violations)
        pytest.fail(
            "Off-policy published runs detected:\n  "
            + listing
            + "\n\nValid model_* statuses: "
            + ", ".join(sorted(INCLUDED_NON_COMPLETED_STATUSES))
            + "\n\nPer SKILL.md these are infra_* failures and should never have "
            "been published; unpublish (git rm) or relabel them."
        )


def test_no_cap_hit_or_auth_failure_signatures_in_published() -> None:
    """No published agent_last_message should contain a known infra signature.

    Even if exit_reason somehow says ``completed``, the actual disqualifier
    text in the agent's last message is grounds for unpublishing. Keeps the
    publish gate's stoplist (``publish._classify_unpublishable_stop_message``)
    honest by checking the same signatures against post-publish data.
    """
    files = _published_run_files()
    if not files:
        pytest.skip("no published runs to check")

    infra_signatures = [
        ("infra_usage_cap", ["you've hit your limit", "usage limit"]),
        ("infra_auth", ["failed to authenticate", "invalid api key", "expired credential"]),
        ("stream_disconnect", ["unable to connect to api", "connectionrefused", "stream disconnected"]),
    ]

    violations: list[str] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        metadata = payload.get("metadata") or {}
        msg = (metadata.get("agent_last_message") or "").lower().replace(" ", " ")
        normalized = msg.replace(" ", "")
        for bucket, needles in infra_signatures:
            for needle in needles:
                needle_norm = needle.replace(" ", "")
                if needle_norm in normalized:
                    violations.append(
                        f"{_row_id(path)}: {bucket} ({needle!r}) in agent_last_message"
                    )
                    break

    if violations:
        listing = "\n  ".join(violations)
        pytest.fail(
            "Published runs carrying infra_* signatures in agent_last_message:\n  "
            + listing
            + "\n\nThese should have been rejected at the publish gate; unpublish them."
        )
