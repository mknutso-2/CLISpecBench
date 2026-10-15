"""Pure advisory gates: no models, credentials, processes, or network calls.

An integration must supply freshly validated observations under the original
shared lock. These objects are not substitutes for substantive review or live
ownership verification, and do not authorize dispatch by themselves.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Usage:
    observed_at: datetime
    expires_at: datetime
    five_hour_percent: float
    weekly_percent: float
    extra_usage_off: bool
    reset_at: datetime | None


@dataclass(frozen=True)
class Operational:
    observed_at: datetime
    frozen_valid: bool
    ownership_known: bool
    lease_valid: bool
    resources_valid: bool
    held: int
    actual_workers: int
    own_workers: int
    own_proxies: int
    own_wrappers: int


@dataclass(frozen=True)
class Review:
    naturally_completed: bool
    grading_complete: bool
    assigned_substantive_valid: bool
    named_peers_valid: bool
    deterministic_evidence_valid: bool
    actual_models_match: bool


@dataclass(frozen=True)
class Decision:
    blockers: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.blockers


def _age(now: datetime, observed_at: datetime) -> float:
    if now.utcoffset() is None or observed_at.utcoffset() is None:
        raise ValueError("timezone_required")
    return (now - observed_at).total_seconds()


def usage_blockers(usage: Usage, now: datetime, *, runway_seconds: int = 1800) -> list[str]:
    blockers: list[str] = []
    if type(runway_seconds) is not int or runway_seconds < 1800:
        raise ValueError("authentication_floor_cannot_be_lowered")
    if not 0 <= _age(now, usage.observed_at) <= 120:
        blockers.append("ordinary_usage_not_fresh")
    if _age(usage.expires_at, now) < runway_seconds:
        blockers.append("authentication_headroom_insufficient")
    if usage.extra_usage_off is not True:
        blockers.append("extra_usage_not_confirmed_off")
    for name, percent in (
        ("five_hour", usage.five_hour_percent),
        ("weekly", usage.weekly_percent),
    ):
        if isinstance(percent, bool) or not math.isfinite(percent) or not 0 <= percent <= 100:
            blockers.append(f"{name}_usage_invalid")
        elif percent > 70:
            blockers.append(f"{name}_reserve_insufficient")
    if usage.reset_at is None:
        if usage.five_hour_percent != 0:
            blockers.append("reset_window_missing")
    elif _age(usage.reset_at, now) <= 0:
        blockers.append("reset_window_expired")
    return blockers


def operational_blockers(snapshot: Operational, now: datetime) -> list[str]:
    blockers: list[str] = []
    if not 0 <= _age(now, snapshot.observed_at) <= 120:
        blockers.append("actual_snapshot_not_fresh")
    for name, valid in (
        ("frozen", snapshot.frozen_valid),
        ("ownership", snapshot.ownership_known),
        ("lease", snapshot.lease_valid),
        ("resources", snapshot.resources_valid),
    ):
        if valid is not True:
            blockers.append(f"{name}_not_validated")
    counts = (
        snapshot.held,
        snapshot.actual_workers,
        snapshot.own_workers,
        snapshot.own_proxies,
        snapshot.own_wrappers,
    )
    if any(type(count) is not int or count < 0 for count in counts):
        blockers.append("worker_counts_invalid")
    elif (
        snapshot.actual_workers > snapshot.held
        or snapshot.own_workers > snapshot.actual_workers
        or snapshot.held > 8
    ):
        blockers.append("global_worker_accounting_invalid")
    return blockers


def dispatch_readiness(
    snapshot: Operational,
    usage: Usage,
    now: datetime,
    *,
    paused: bool,
    stopped: bool,
    target_unreserved: bool,
    authorized_target: bool,
    runway_seconds: int = 1800,
) -> Decision:
    blockers = operational_blockers(snapshot, now) + usage_blockers(
        usage, now, runway_seconds=runway_seconds
    )
    for code, blocked in (
        ("collection_paused", paused is not False),
        ("collection_stopped", stopped is not False),
        ("target_already_reserved", target_unreserved is not True),
        ("target_not_authorized", authorized_target is not True),
        ("global_held_ceiling", snapshot.held >= 8),
    ):
        if blocked:
            blockers.append(code)
    return Decision(tuple(blockers))


def finalization_readiness(
    snapshot: Operational,
    usage: Usage,
    review: Review,
    now: datetime,
    *,
    paused: bool,
    stopped: bool,
    own_record_held: bool,
) -> Decision:
    """Ceiling/exhaustion affect DISPATCH, never release of a reviewed own cell."""
    blockers = operational_blockers(snapshot, now) + usage_blockers(usage, now)
    for code, valid in (
        ("collection_not_paused", paused is False),
        ("collection_not_stopped", stopped is False),
        ("own_record_held", own_record_held is True and snapshot.held > 0),
        ("natural_completion", review.naturally_completed),
        ("grading_complete", review.grading_complete),
        ("substantive_review", review.assigned_substantive_valid),
        ("named_exception_peers", review.named_peers_valid),
        ("strict_evidence", review.deterministic_evidence_valid),
        ("same_model", review.actual_models_match),
        (
            "own_actual_drain",
            snapshot.own_workers == snapshot.own_proxies == snapshot.own_wrappers == 0,
        ),
    ):
        if valid is not True:
            blockers.append(code)
    return Decision(tuple(blockers))
