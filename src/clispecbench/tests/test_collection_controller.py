"""API-free replays of Haiku controller failures; no submitted code is loaded."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from clispecbench.collection.evidence import Artifact, EvidenceStore, Journal, digest
from clispecbench.collection.readiness import (
    Operational,
    Review,
    Usage,
    dispatch_readiness,
    finalization_readiness,
    operational_blockers,
    usage_blockers,
)

NOW = datetime(2026, 10, 11, 1, 0, tzinfo=UTC)
USAGE = Usage(NOW, NOW + timedelta(hours=4), 10, 12, True, NOW + timedelta(hours=2))
SNAPSHOT = Operational(NOW, True, True, True, True, 1, 0, 0, 0, 0)
REVIEW = Review(True, True, True, True, True, True)


def dispatch(snapshot: Operational = SNAPSHOT, usage: Usage = USAGE):
    return dispatch_readiness(
        snapshot,
        usage,
        NOW,
        paused=False,
        stopped=False,
        target_unreserved=True,
        authorized_target=True,
    )


def finalize(snapshot: Operational = SNAPSHOT, review: Review = REVIEW):
    return finalization_readiness(
        snapshot, USAGE, review, NOW, paused=False, stopped=False, own_record_held=True
    )


def test_exact_utf8_signed_bytes_survive_large_transport(tmp_path: Path) -> None:
    # A real validator is provided by the collection integration, not this unit fixture.
    raw = ('{"number":1.0000000000000001,"text":"§' + "x" * 1_000_000 + '"}\n').encode()
    calls: list[bytes] = []

    def validate(data: bytes) -> None:
        assert data == raw
        calls.append(data)

    store = EvidenceStore(tmp_path)
    artifact = store.save_review("reviews/one.json", raw, digest(raw), validate)
    assert (tmp_path / "reviews/one.json").read_bytes() == raw
    assert store.get(artifact.sha256) == raw
    assert len(calls) == 2
    # Idempotent recovery never rewrites/restamps the existing body.
    store.save_review("reviews/one.json", raw, digest(raw), validate)


def test_bad_candidate_cannot_be_saved(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)

    def reject(_: bytes) -> None:
        raise ValueError("strict_review_rejected")

    with pytest.raises(ValueError, match="strict_review_rejected"):
        store.save_review("review.json", b"{}", digest(b"{}"), reject)
    assert not (tmp_path / "review.json").exists()
    with pytest.raises(ValueError, match="transport_hash"):
        store.save_review("review.json", b"{}", digest(b"different"), reject)


def test_existing_final_is_immutable(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    store.save_review("review.json", b"{}", digest(b"{}"), lambda _: None)
    with pytest.raises(ValueError, match="existing_review_conflict"):
        store.save_review("review.json", b'{"new":true}', digest(b'{"new":true}'), lambda _: None)
    assert (tmp_path / "review.json").read_bytes() == b"{}"


@pytest.mark.parametrize("path", ["../outside.json", "objects/one.json", "."])
def test_review_path_cannot_escape_or_use_reserved_names(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError, match="review_path"):
        EvidenceStore(tmp_path).save_review(path, b"{}", digest(b"{}"), lambda _: None)


def test_object_tampering_rejected(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    artifact = store.put(b"original")
    path = tmp_path / "objects" / artifact.sha256[:2] / artifact.sha256
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="evidence_hash_mismatch"):
        store.get(artifact.sha256)


def test_journal_restart_and_stale_head(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence")
    journal = Journal(tmp_path / "journal", store)
    artifact = store.put(b"preserved launch receipt")
    first = journal.append("reserved", artifact, expected_head=None)
    second = journal.append("started", artifact, expected_head=first.sha256)
    assert Journal(tmp_path / "journal", store).load() == (first, second)
    with pytest.raises(ValueError, match="journal_head_changed"):
        journal.append("started", artifact, expected_head=first.sha256)
    assert len(journal.load()) == 2


def test_two_coordinators_cannot_replace_same_event(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence")
    journal = Journal(tmp_path / "journal", store)
    artifact = store.put(b"same target; no second model attempt")

    def append(_: int) -> bool:
        try:
            journal.append("reserved", artifact, expected_head=None)
            return True
        except (ValueError, FileExistsError):
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(append, (1, 2))) == 1
    assert len(journal.load()) == 1


def test_journal_corruption_and_duplicate_keys_rejected(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence")
    journal = Journal(tmp_path / "journal", store)
    artifact = store.put(b"{}")
    journal.append("prepared", artifact, expected_head=None)
    path = tmp_path / "journal/00000001.json"
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + b',"kind":"paused"}')
    with pytest.raises(ValueError, match="duplicate_json_key"):
        journal.load()
    path.write_bytes(raw)
    path.rename(path.with_name("00000002.json"))
    with pytest.raises(ValueError, match="sequence_gap"):
        journal.load()


def test_journal_has_only_fixed_codes_and_artifact_references(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence")
    journal = Journal(tmp_path / "journal", store)
    artifact = store.put(b"private evidence")
    with pytest.raises(ValueError, match="kind_invalid"):
        journal.append("arbitrary exception/credential text", artifact, expected_head=None)
    with pytest.raises(ValueError, match="artifact_size"):
        journal.append("held", Artifact(artifact.sha256, -1), expected_head=None)
    journal.append("held", artifact, expected_head=None)
    saved = json.loads((tmp_path / "journal/00000001.json").read_bytes())
    assert set(saved) == {"sequence", "previous", "kind", "artifact_sha256", "artifact_size"}


def test_interrupted_pending_writes_are_not_committed_events(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence")
    directory = tmp_path / "journal"
    directory.mkdir()
    (directory / ".pending-interrupted").write_bytes(b"incomplete")
    journal = Journal(directory, store)
    assert journal.load() == ()
    first = journal.append("held", store.put(b"preserved receipt"), expected_head=None)
    assert journal.load() == (first,)
    assert (directory / ".pending-interrupted").read_bytes() == b"incomplete"


def test_external_expected_head_detects_deleted_journal_tail(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence")
    journal = Journal(tmp_path / "journal", store)
    artifact = store.put(b"preserved receipt")
    first = journal.append("reserved", artifact, expected_head=None)
    second = journal.append("started", artifact, expected_head=first.sha256)
    (tmp_path / "journal/00000002.json").unlink()
    with pytest.raises(ValueError, match="journal_head_changed"):
        journal.append("completed", artifact, expected_head=second.sha256)


def test_review_validator_failure_after_save_does_not_clobber_evidence(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    calls = 0

    def validate(_: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("post_save_check_failed")

    with pytest.raises(ValueError, match="post_save_check_failed"):
        store.save_review("review.json", b"{}", digest(b"{}"), validate)
    assert (tmp_path / "review.json").read_bytes() == b"{}"
    assert store.get(digest(b"{}")) == b"{}"


@pytest.mark.parametrize("held", [1, 8])
def test_completed_own_review_can_release_at_ceiling_or_queue_exhaustion(held: int) -> None:
    snapshot = replace(SNAPSHOT, held=held, actual_workers=held - 1)
    assert finalize(snapshot).ready
    exhausted = dispatch_readiness(
        snapshot,
        USAGE,
        NOW,
        paused=False,
        stopped=False,
        target_unreserved=True,
        authorized_target=False,
    )
    assert not exhausted.ready
    if held == 8:
        assert "global_held_ceiling" in exhausted.blockers


@pytest.mark.parametrize("field", ["own_workers", "own_proxies", "own_wrappers"])
def test_no_release_before_all_own_worker_types_drain(field: str) -> None:
    snapshot = replace(SNAPSHOT, actual_workers=1, **{field: 1})
    assert not finalize(snapshot).ready


@pytest.mark.parametrize(
    "field",
    [
        "naturally_completed",
        "grading_complete",
        "assigned_substantive_valid",
        "named_peers_valid",
        "deterministic_evidence_valid",
        "actual_models_match",
    ],
)
def test_model_error_mixed_model_and_incomplete_reviews_remain_held(field: str) -> None:
    assert not finalize(review=replace(REVIEW, **{field: False})).ready


@pytest.mark.parametrize("paused,stopped", [(True, False), (False, True), (True, True)])
def test_pause_and_stop_not_bypassed_for_dispatch_or_review(paused: bool, stopped: bool) -> None:
    assert not dispatch_readiness(
        SNAPSHOT,
        USAGE,
        NOW,
        paused=paused,
        stopped=stopped,
        target_unreserved=True,
        authorized_target=True,
    ).ready
    assert not finalization_readiness(
        SNAPSHOT,
        USAGE,
        REVIEW,
        NOW,
        paused=paused,
        stopped=stopped,
        own_record_held=True,
    ).ready


@pytest.mark.parametrize("seconds", [-1, 121, 155, 627])
def test_slow_validation_or_future_clock_cannot_fake_fresh_usage(seconds: int) -> None:
    assert not dispatch(usage=replace(USAGE, observed_at=NOW - timedelta(seconds=seconds))).ready


def test_late_usage_after_expensive_validation_keeps_real_120_second_rule() -> None:
    assert not dispatch(usage=replace(USAGE, observed_at=NOW - timedelta(seconds=155))).ready
    assert dispatch().ready
    assert dispatch(usage=replace(USAGE, observed_at=NOW - timedelta(seconds=120))).ready
    assert not finalize(snapshot=replace(SNAPSHOT, observed_at=NOW - timedelta(seconds=121))).ready


@pytest.mark.parametrize("percent", [71, 100, float("nan"), float("inf"), -1, True])
def test_quota_unknown_invalid_and_insufficient_reserve(percent: float) -> None:
    assert not dispatch(usage=replace(USAGE, five_hour_percent=percent)).ready
    assert not dispatch(usage=replace(USAGE, weekly_percent=percent)).ready


def test_authentication_runway_is_tightenable_not_looseneable() -> None:
    near_expiry = replace(USAGE, expires_at=NOW + timedelta(seconds=1799))
    assert not dispatch(usage=near_expiry).ready
    assert dispatch(usage=replace(USAGE, expires_at=NOW + timedelta(seconds=1800))).ready
    with pytest.raises(ValueError, match="floor_cannot_be_lowered"):
        usage_blockers(USAGE, NOW, runway_seconds=60)
    assert "authentication_headroom_insufficient" in usage_blockers(
        USAGE, NOW, runway_seconds=5 * 3600
    )


@pytest.mark.parametrize("runway", [float("nan"), float("inf"), 1800.0, True])
def test_authentication_runway_requires_an_integer(runway: object) -> None:
    # Deliberate malformed boundary input cannot weaken the auth floor.
    with pytest.raises(ValueError, match="floor_cannot_be_lowered"):
        usage_blockers(USAGE, NOW, runway_seconds=runway)  # type: ignore[arg-type]


def test_reset_extra_usage_and_unknown_backend_fail_closed() -> None:
    assert not dispatch(usage=replace(USAGE, extra_usage_off=False)).ready
    assert not dispatch(usage=replace(USAGE, reset_at=NOW)).ready
    assert not dispatch(usage=replace(USAGE, reset_at=None)).ready
    assert dispatch(usage=replace(USAGE, reset_at=None, five_hour_percent=0)).ready
    for field in ("frozen_valid", "ownership_known", "lease_valid", "resources_valid"):
        assert not dispatch(snapshot=replace(SNAPSHOT, **{field: False})).ready


@pytest.mark.parametrize("held,actual,own", [(9, 0, 0), (1, 2, 0), (0, 0, 1), (-1, 0, 0)])
def test_unknown_or_inconsistent_global_worker_counts(held: int, actual: int, own: int) -> None:
    assert operational_blockers(
        replace(SNAPSHOT, held=held, actual_workers=actual, own_workers=own), NOW
    )


def test_naive_datetimes_cannot_bypass_freshness() -> None:
    with pytest.raises(ValueError, match="timezone_required"):
        usage_blockers(USAGE, NOW.replace(tzinfo=None))
