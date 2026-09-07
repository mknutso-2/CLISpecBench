"""Explicit, preflight-validated RS274 3.2.2 publication; dry-run unless --apply.

This migration reads the audit archive once. Dashboard builders continue to
read published_results only. Original generation metadata is never rewritten.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COHORTS = ("gpt-6-astra", "gpt-5.6-codex-cli", "historical", "historical-rs-older-prompt")
UNREGRADEABLE = {
    "79266582-254d-4b07-9834-af8d1bf7ad3c",
    "fe7bf6d1-bc3e-46c3-886a-86c4db28efd1",
}
TEST_SHA = "3d096665fab1578444b0c0a0f7bfa1975e389a9398a34e265820305b300eca11"


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def promote(
    original: dict[str, Any],
    record: dict[str, Any],
    *,
    record_path: str,
    record_sha: str,
    revision: str,
    cohort: str,
) -> dict[str, Any]:
    """Replace grading only, retaining prior publication context for audit."""
    if original.get("regrade"):
        raise ValueError("Already promoted; refusing to overwrite grading history")
    if original["metadata"]["run_uid"] != record["original"]["run_uid"]:
        raise ValueError("Run UID mismatch")
    grading = record["grading"]
    if grading["status"] != "completed" or grading["eval_version"] != "3.2.2":
        raise ValueError("Expected completed 3.2.2 grading")
    if grading["test_suite_sha"] != TEST_SHA:
        raise ValueError("Unexpected test suite")
    tests, summary = record["tests"], record["test_summary"]
    counts = Counter(t["outcome"] for t in tests)
    if len(tests) != 555 or len({t["node_id"] for t in tests}) != 555:
        raise ValueError("Expected 555 unique outcomes")
    if summary["total"] != 555 or summary["skipped"]:
        raise ValueError("Incomplete grading")
    if any(counts[k] != summary[k] for k in ("passed", "failed", "error", "skipped")):
        raise ValueError("Outcome/summary mismatch")
    for key in ("correctness", "task_score"):
        if abs(record["scores"][key] - summary["passed"] / 555) > 1e-9:
            raise ValueError("Score mismatch")
    comparison = record["comparison"]
    if comparison["additional_model_calls"] != 0 or comparison["additional_model_cost_usd"] != 0:
        raise ValueError("Not a zero-inference regrade")
    if cohort != "historical-rs-older-prompt" and not comparison["model_input_unchanged"]:
        raise ValueError("Unexpected prompt mismatch")
    result = copy.deepcopy(original)
    result["regrade"] = {
        "regrade_uid": record["regrade_uid"],
        "grading": copy.deepcopy(grading),
        "audit_record": record_path,
        "audit_record_sha256": record_sha,
        "original_published_sha256": record["original"]["published_result_sha256"],
        "original_git_revision": revision,
        "original_test_summary": original["test_summary"],
        "original_scores": original["scores"],
        "original_editorial": original.get("editorial", {}),
        "source_content_sha": record["original"]["source_content_sha"],
        "model_input_unchanged": comparison["model_input_unchanged"],
        "additional_model_calls": 0,
        "additional_model_cost_usd": 0,
        "comparison_cohort": "older Rust prompt 35713dbfd826"
        if cohort == "historical-rs-older-prompt"
        else "",
    }
    for field in ("tests", "test_summary", "scores"):
        result[field] = copy.deepcopy(record[field])
    editorial = result.setdefault("editorial", {})
    old_message = editorial.get("last_message") or "No original editorial assessment."
    version = original["metadata"]["eval_version"]
    editorial["last_message"] = (
        f"Regraded unchanged source under RS274 3.2.2: {summary['passed']}/555. "
        f"Original {version} assessment (historical): {old_message}"
    )
    return result


def plan(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    published = root / "published_results"
    paths = sorted(published.glob("rs274-*/*/*/run*.json"))
    originals = {read(p)["metadata"]["run_uid"]: p for p in paths}
    if len(originals) != len(paths) or len(paths) != 387:
        raise ValueError("Expected exactly 387 unique published RS274 runs")
    pending: list[tuple[Path, dict[str, Any]]] = []
    seen: set[str] = set()
    for cohort in COHORTS:
        for record_path in sorted((root / "regraded_results/rs274/3.2.2" / cohort).glob("*.json")):
            record = read(record_path)
            if record.get("artifact_type") != "clispecbench.regrade-summary":
                continue
            uid = record["original"]["run_uid"]
            if uid in seen or uid not in originals:
                raise ValueError(f"Unexpected or duplicate UID: {uid}")
            seen.add(uid)
            target = (root / record["original"]["published_result"]).resolve()
            if target != originals[uid].resolve():
                raise ValueError(f"Target path mismatch: {uid}")
            current = read(target)
            prior_revision = revision
            original_bytes = target.read_bytes()
            if current.get("regrade"):
                prior_revision = current["regrade"]["original_git_revision"]
                if not re.fullmatch(r"[0-9a-f]{40}", prior_revision):
                    raise ValueError("Invalid original Git revision")
                original_bytes = subprocess.check_output(
                    ["git", "show", f"{prior_revision}:{target.relative_to(root).as_posix()}"],
                    cwd=root,
                )
                # The initial promotion verifies raw checkout bytes. Git may
                # normalize even mixed line endings, so resume instead verifies
                # the entire expected JSON replacement against the current file
                # below (including original metadata, scores and editorial).
            if (
                not current.get("regrade")
                and hashlib.sha256(original_bytes).hexdigest()
                != record["original"]["published_result_sha256"]
            ):
                raise ValueError(f"Original publication changed: {target}")
            replacement = promote(
                json.loads(original_bytes),
                record,
                record_path=record_path.relative_to(root).as_posix(),
                record_sha=hashlib.sha256(record_path.read_bytes()).hexdigest(),
                revision=prior_revision,
                cohort=cohort,
            )
            if current.get("regrade") and current != replacement:
                raise ValueError(f"Previously promoted record differs: {target}")
            pending.append((target, replacement))
    if len(seen) != 385 or originals.keys() - seen != UNREGRADEABLE:
        raise ValueError("Cohort coverage differs from the approved migration")
    for uid in sorted(UNREGRADEABLE):
        path = originals[uid]
        original = read(path)
        original.setdefault("editorial", {})["comparison_cohort"] = (
            "historical grading; no saved source"
        )
        pending.append((path, original))
    return pending


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write the validated migration")
    args = parser.parse_args()
    pending = plan(ROOT)  # Validate the entire cohort before the first write.
    print(f"Validated {len(pending)} rows: 385 regrades, 2 labelled historical exceptions")
    if args.apply:
        for path, result in pending:
            # Atomic per-file replacement; a later failure is safely resumable.
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(json.dumps(result, indent=2) + "\n")
            try:
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        print("Promoted. Rebuild the dashboard before committing and deploying.")
    else:
        print("Dry run only; pass --apply to promote.")


if __name__ == "__main__":
    main()
