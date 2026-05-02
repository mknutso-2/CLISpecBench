"""CLI entry point for clispecbench."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from clispecbench.agents.base import AgentAdapter
from clispecbench.agents.registry import get_agent_spec, list_agent_ids
from clispecbench.harness.flakiness import compute_flakiness
from clispecbench.harness.hashing import hash_prompt_content, hash_test_suite
from clispecbench.harness.publish import PublishError, publish_result
from clispecbench.harness.results import (
    EvalLock,
    RunResult,
    load_result,
    next_eval_number,
    result_path,
)
from clispecbench.harness.runner import run_evaluation
from clispecbench.harness.scoring import compute_subscores
from clispecbench.harness.task import list_evals, list_languages, resolve_task


def _find_repo_root() -> Path:
    """Walk up from cwd to find the repo root (directory containing AGENTS.md)."""
    p = Path.cwd()
    while p != p.parent:
        if (p / "AGENTS.md").is_file():
            return p
        p = p.parent
    return Path.cwd()


def _get_adapter(
    agent_name: str,
    model: str | None = None,
    effort: str | None = None,
) -> AgentAdapter:
    """Resolve an agent name to an adapter instance."""
    try:
        spec = get_agent_spec(agent_name)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    return spec.create(model=model, effort=effort)


# ---------------------------------------------------------------------------
# Subcommand: run
# ---------------------------------------------------------------------------


def _cmd_run(args: argparse.Namespace) -> None:
    repo_root = _find_repo_root()
    task = resolve_task(repo_root, args.task, language=getattr(args, "language", None))
    adapter = _get_adapter(
        args.agent,
        model=getattr(args, "model", None),
        effort=getattr(args, "effort", None),
    )

    api_key_env: dict[str, str] = {}
    raw_keys: list[str] = args.api_key_env or []
    for kv in raw_keys:
        if "=" not in kv:
            print(f"Invalid --api-key-env format: {kv!r} (expected VAR=value)", file=sys.stderr)
            sys.exit(1)
        key, value = kv.split("=", 1)
        api_key_env[key] = value

    num_runs: int = args.runs
    output_dir = Path(args.output_dir)

    # Acquire a filesystem lock to prevent concurrent runs for the same config.
    lock = EvalLock.acquire(
        output_dir,
        task.task_id,
        adapter.name,
        adapter.model,
        adapter.effort,
    )
    try:
        eval_num = next_eval_number(
            output_dir,
            task.task_id,
            adapter.name,
            adapter.model,
            adapter.effort,
        )
        log = logging.getLogger(__name__)
        log.info("Writing results to eval%d (runs 1-%d)", eval_num, num_runs)

        for run_number in range(1, num_runs + 1):
            print(f"\n{'=' * 60}")
            print(
                f"eval{eval_num}/run{run_number} ({run_number}/{num_runs}): "
                f"{args.task} / {adapter.name}"
            )
            print(f"{'=' * 60}\n")

            result = run_evaluation(
                task=task,
                adapter=adapter,
                run_number=run_number,
                eval_number=eval_num,
                prompt_variant=args.prompt_variant,
                output_dir=Path(args.output_dir),
                api_key_env=api_key_env,
                skip_extensions=args.skip_extensions,
            )

            print(f"\nResult: {result.metadata.exit_reason}")
            print(f"Tests: {result.test_summary.passed}/{result.test_summary.total} passed")
            if result.scores.task_score is not None:
                print(f"Task score: {result.scores.task_score:.3f}")
            if result.token_usage:
                print(f"Tokens: {result.token_usage.total_tokens:,}")

            # Write a progress file next to the results so external observers
            # can tell the eval is alive and how far along it is without
            # parsing stdout.
            progress_path = (
                result_path(
                    output_dir,
                    task.task_id,
                    adapter.name,
                    run_number,
                    adapter.model,
                    adapter.effort,
                    eval_num,
                ).parent.parent
                / "progress.txt"
            )
            progress_path.write_text(
                f"run {run_number}/{num_runs} completed\n"
                f"last: {result.test_summary.passed}/{result.test_summary.total} "
                f"({result.metadata.exit_reason})\n",
                encoding="utf-8",
            )
    finally:
        lock.release()


# ---------------------------------------------------------------------------
# Subcommand: results
# ---------------------------------------------------------------------------


def _run_label(r: RunResult, path: Path) -> str:
    """Short, unique label for a run in the breakdown header.

    Includes model (if set) and the eval dir name from the path so that
    multiple runs of the same agent don't collide into identical columns.
    Example: ``gemini-cli/gemini-3-flash-preview/eval1r1``.
    """
    parts = [r.metadata.agent]
    if r.metadata.model:
        parts.append(r.metadata.model)
    # Find an eval<N> segment in the path, if present.
    eval_seg = next(
        (p.name for p in path.parents if p.name.startswith("eval")),
        None,
    )
    tail = f"{eval_seg}r{r.metadata.run_number}" if eval_seg else f"r{r.metadata.run_number}"
    parts.append(tail)
    return "/".join(parts)


def _collect_breakdown(
    results: list[tuple[RunResult, Path]],
) -> tuple[list[tuple[str, dict[str, tuple[int, int]]]], list[str]]:
    """Extract per-run subscores + the sorted bucket list from filtered results."""
    per_run: list[tuple[str, dict[str, tuple[int, int]]]] = []
    all_buckets: set[str] = set()
    for r, path in results:
        buckets: dict[str, tuple[int, int]] = {}
        ext = r.scores.extension_scores
        for key, val in ext.items():
            if not key.startswith("subscore.") or not key.endswith(".passed"):
                continue
            bucket = key[len("subscore.") : -len(".passed")]
            total_key = f"subscore.{bucket}.total"
            if total_key not in ext:
                continue
            buckets[bucket] = (int(val), int(ext[total_key]))
        if not buckets:
            continue
        per_run.append((_run_label(r, path), buckets))
        all_buckets.update(buckets)
    return per_run, sorted(all_buckets)


def _print_breakdown_csv(results: list[tuple[RunResult, Path]]) -> None:
    """Emit the breakdown as CSV: one row per capability, two columns per run
    (``<label> passed`` + ``<label> total``). Numeric so it sorts/filters/
    color-scales cleanly in Excel and Google Sheets. Callers add ``=B2/C2``
    for percentages if they want them."""
    import csv

    per_run, buckets = _collect_breakdown(results)
    if not per_run:
        print("No subscore data found in matching results.", file=sys.stderr)
        return

    writer = csv.writer(sys.stdout, lineterminator="\n")
    header: list[str] = ["capability"]
    for label, _ in per_run:
        header.append(f"{label} passed")
        header.append(f"{label} total")
    writer.writerow(header)

    for bucket in buckets:
        row: list[str] = [bucket]
        for _, run_buckets in per_run:
            if bucket in run_buckets:
                p, t = run_buckets[bucket]
                row.append(str(p))
                row.append(str(t))
            else:
                row.append("")
                row.append("")
        writer.writerow(row)


def _eval_seg_from_path(path: Path) -> str:
    """Return the ``evalN`` path segment for a result, or ``eval?`` if absent."""
    for p in path.parents:
        if p.name.startswith("eval"):
            return p.name
    return "eval?"


def _print_flakiness(results: list[tuple[RunResult, Path]]) -> None:
    """Group runs by (task, agent, model, eval) and flag tests whose
    outcomes aren't unanimous across the runs in each group.

    Only groups with at least 2 runs are analyzed; groups with a single
    run are listed as "not enough runs" so the user can see at a glance
    which configurations are missing repeat data.
    """
    # Group key: (task, agent, model, eval_segment).
    groups: dict[tuple[str, str, str, str], list[RunResult]] = {}
    for r, path in results:
        key = (
            r.metadata.task,
            r.metadata.agent,
            r.metadata.model or "-",
            _eval_seg_from_path(path),
        )
        groups.setdefault(key, []).append(r)

    if not groups:
        print("No matching results found.")
        return

    analyzed = 0
    total_flaky = 0
    total_tests = 0
    for key in sorted(groups):
        task, agent, model, eval_seg = key
        runs = sorted(groups[key], key=lambda r: r.metadata.run_number)
        header = f"{task} / {agent} / {model} / {eval_seg}"
        if len(runs) < 2:
            print(f"{header}  (1 run -- not enough for flakiness)")
            continue
        analyzed += 1
        report = compute_flakiness(runs)
        total_flaky += len(report.flaky)
        total_tests += report.total_tests

        n_runs = len(runs)
        print(f"{header}  ({n_runs} runs)")
        if not report.flaky:
            print(f"  all {report.total_tests} tests stable")
            print()
            continue

        # If every flaky test has the same pattern, it's almost certainly a
        # structural issue (whole run crashed / container failure / network
        # blip) rather than independent per-test flakes. Collapse into one
        # line so 400 identical rows don't bury a real signal elsewhere.
        unique_patterns = {f.pattern for f in report.flaky}
        if len(unique_patterns) == 1 and len(report.flaky) >= 3:
            (pattern,) = unique_patterns
            note = ""
            if "E" in pattern:
                note = "  (likely a crashed run, not per-test flakiness)"
            print(
                f"  {len(report.flaky)} tests all flipped identically with pattern {pattern}{note}"
            )
            print(
                f"  ({report.stable_count} stable, {len(report.flaky)} flaky "
                f"of {report.total_tests} total)"
            )
            print()
            continue

        width = max(len(f.node_id) for f in report.flaky)
        print(f"  {'pattern':<{n_runs + 2}}  {'test':<{width}}")
        for f in report.flaky:
            print(f"  {f.pattern:<{n_runs + 2}}  {f.node_id}")
        print(
            f"  ({report.stable_count} stable, {len(report.flaky)} flaky "
            f"of {report.total_tests} total)"
        )
        print()

    if analyzed:
        print(
            f"Analyzed {analyzed} group(s) with repeat runs: "
            f"{total_flaky} flaky test(s) across {total_tests} total."
        )
    else:
        print(
            "No groups had multiple runs -- flakiness requires at least 2 "
            "runs of the same (task, agent, model, eval)."
        )


def _print_breakdown(results: list[tuple[RunResult, Path]]) -> None:
    """Per-capability subscore table across the filtered runs.

    Reads ``subscore.<bucket>.passed`` / ``subscore.<bucket>.total`` pairs
    out of ``scores.extension_scores`` and pivots them into a
    ``capability x run`` table.
    """
    per_run, sorted_buckets = _collect_breakdown(results)
    all_buckets = set(sorted_buckets)

    if not per_run:
        print("No subscore data found in matching results.")
        print("(Subscores are populated for runs produced after the feature was added.)")
        return

    bucket_width = max((len(b) for b in all_buckets), default=0)
    bucket_width = max(bucket_width, len("capability"))
    # Each column's width = max(label, widest cell, minimum).
    col_widths: list[int] = []
    for label, buckets in per_run:
        widest_cell = 0
        for b in all_buckets:
            if b not in buckets:
                widest_cell = max(widest_cell, 1)
                continue
            p, t = buckets[b]
            pct = (p / t * 100) if t else 0.0
            widest_cell = max(widest_cell, len(f"{p}/{t} ({pct:.0f}%)"))
        col_widths.append(max(len(label), widest_cell, 12))

    header = f"{'capability':<{bucket_width}}  " + "  ".join(
        f"{label:<{w}}" for (label, _), w in zip(per_run, col_widths, strict=True)
    )
    print(header)
    print("-" * len(header))
    for bucket in sorted_buckets:
        cells: list[str] = []
        for (_, buckets), w in zip(per_run, col_widths, strict=True):
            if bucket not in buckets:
                cells.append(f"{'-':<{w}}")
                continue
            p, t = buckets[bucket]
            pct = (p / t * 100) if t else 0.0
            cells.append(f"{f'{p}/{t} ({pct:.0f}%)':<{w}}")
        print(f"{bucket:<{bucket_width}}  " + "  ".join(cells))


def _cmd_results(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    if not output_dir.is_dir():
        print(f"No results directory found at {output_dir}", file=sys.stderr)
        sys.exit(1)

    # Collect all result files matching filters
    results: list[tuple[RunResult, Path]] = []
    for json_file in sorted(output_dir.rglob("result.json")):
        try:
            r = load_result(json_file)
        except Exception as exc:
            print(f"Warning: skipping {json_file}: {exc}", file=sys.stderr)
            continue
        if args.task and r.metadata.task != args.task:
            continue
        if args.agent and r.metadata.agent != args.agent:
            continue
        results.append((r, json_file))

    if not results:
        print("No matching results found.")
        return

    if args.breakdown:
        if args.format == "csv":
            _print_breakdown_csv(results)
        elif args.format == "table":
            _print_breakdown(results)
        else:
            print(
                f"--breakdown does not support --format {args.format} (use 'table' or 'csv')",
                file=sys.stderr,
            )
            sys.exit(2)
        return

    if args.flakiness:
        _print_flakiness(results)
        return

    # Print table
    print(
        f"{'Task':<20} {'Agent':<15} {'Run':<5} {'Pass':<6} {'Total':<6} "
        f"{'Score':<8} {'Tokens':<10} {'Exit':<10}"
    )
    print("-" * 90)
    for r, _ in results:
        tokens = f"{r.token_usage.total_tokens:,}" if r.token_usage else "n/a"
        score = f"{r.scores.task_score:.3f}" if r.scores.task_score is not None else "n/a"
        print(
            f"{r.metadata.task:<20} {r.metadata.agent:<15} {r.metadata.run_number:<5} "
            f"{r.test_summary.passed:<6} {r.test_summary.total:<6} "
            f"{score:<8} {tokens:<10} {r.metadata.exit_reason:<10}"
        )


# ---------------------------------------------------------------------------
# Subcommand: validate
# ---------------------------------------------------------------------------


def _cmd_backfill_subscores(args: argparse.Namespace) -> None:
    """Backfill per-capability subscores into existing result.json files.

    Walks ``--output-dir`` for every ``result.json``, re-runs
    :func:`compute_subscores` on the stored ``tests`` list, and merges the
    resulting ``subscore.*`` keys into ``scores.extension_scores``. This is
    a pure function of data already in the file, so a fresh run would
    produce byte-identical subscore values.

    Idempotent: files that already have ``subscore.*`` keys are skipped
    unless ``--force`` is passed. Prints one line per file so the user can
    audit what changed; ``--dry-run`` prints without writing.
    """
    import json

    output_dir = Path(args.output_dir)
    if not output_dir.is_dir():
        print(f"No results directory found at {output_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(output_dir.rglob("result.json"))
    if not files:
        print(f"No result.json files under {output_dir}")
        return

    n_updated = 0
    n_skipped_existing = 0
    n_skipped_notests = 0
    n_errors = 0

    for f in files:
        rel = f.relative_to(output_dir)
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  error  {rel}: could not parse ({exc})")
            n_errors += 1
            continue

        raw_scores = data.get("scores")
        scores_obj: dict[str, object] = {}
        if isinstance(raw_scores, dict):
            for k, v in raw_scores.items():  # pyright: ignore[reportUnknownVariableType]
                if isinstance(k, str):
                    scores_obj[k] = v
        raw_ext = scores_obj.get("extension_scores")
        ext: dict[str, float] = {}
        if isinstance(raw_ext, dict):
            for k, v in raw_ext.items():  # pyright: ignore[reportUnknownVariableType]
                if isinstance(k, str) and isinstance(v, (int, float)):
                    ext[k] = float(v)
        has_subscores = any(k.startswith("subscore.") for k in ext)
        if has_subscores and not args.force:
            print(f"  skip   {rel}  (already has subscores)")
            n_skipped_existing += 1
            continue

        # Rebuild TestOutcome list from the stored JSON directly rather than
        # going through load_result → to_dict, which is lossier than just
        # mutating the dict we already have.
        try:
            result = load_result(f)
        except Exception as exc:
            print(f"  error  {rel}: load_result failed ({exc})")
            n_errors += 1
            continue

        if not result.tests:
            print(f"  skip   {rel}  (no tests recorded)")
            n_skipped_notests += 1
            continue

        subscores = compute_subscores(result.tests)
        if not subscores:
            print(f"  skip   {rel}  (no classifiable test buckets)")
            n_skipped_notests += 1
            continue

        # Merge into the raw dict and write back — preserves any fields we
        # don't know about (forward-compat with future schema additions).
        ext.update(subscores)
        scores_obj["extension_scores"] = ext
        data["scores"] = scores_obj

        n_buckets = sum(1 for k in subscores if k.endswith(".passed"))
        if args.dry_run:
            print(f"  DRY    {rel}  (+{n_buckets} buckets)")
        else:
            f.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"  ok     {rel}  (+{n_buckets} buckets)")
        n_updated += 1

    print()
    verb = "would update" if args.dry_run else "updated"
    print(
        f"{verb}: {n_updated}   skipped-existing: {n_skipped_existing}   "
        f"skipped-empty: {n_skipped_notests}   errors: {n_errors}"
    )


def _cmd_hash(args: argparse.Namespace) -> None:
    """Print content hashes for a task's prompt + test suite.

    Useful for verifying that two runs were actually scored against the same
    bytes, independent of the manual ``eval_version`` bump. With
    ``--show-manifest`` the full per-file manifest is dumped so a human can
    eyeball exactly which files feed the hash.
    """
    repo_root = _find_repo_root()
    task = resolve_task(repo_root, args.task, language=getattr(args, "language", None))
    prompt = hash_prompt_content(task, args.prompt_variant)
    tests = hash_test_suite(task)
    print(f"task:               {task.task_id}")
    print(f"eval_version:       {task.version}")
    print(f"prompt_content_sha: {prompt.sha256}")
    print(f"test_suite_sha:     {tests.sha256}")
    if args.show_manifest:
        print("\n--- prompt manifest ---")
        print(prompt.manifest, end="")
        print("\n--- test-suite manifest ---")
        print(tests.manifest, end="")


DEFAULT_PUBLISHED_DIR = "published_results"


def _rebuild_dashboard_data(repo_root: Path) -> int:
    """Regenerate ``results-published.json`` and ``test-results-published.json``.

    The dashboard reads those two files; they're built from ``published_results/``
    by two scripts in ``published_results/web/``. ``clispecbench publish`` only
    writes the per-run files, so the dashboard goes stale until these are
    rebuilt. This helper runs both scripts, in order, with the active uv
    environment so they pick up the right Python.

    Returns 0 on success, non-zero if either script fails. Writes its own
    diagnostics to stderr so the caller can surface a clean message.
    """
    import subprocess

    web_dir = repo_root / "published_results" / "web"
    scripts = [
        web_dir / "build_results_json.py",
        web_dir / "build_test_results_json.py",
    ]
    for script in scripts:
        if not script.is_file():
            print(f"rebuild-dashboard: missing {script}", file=sys.stderr)
            return 1
        # Use the same interpreter we're running under so the script gets the
        # right env (uv-managed venv, project deps, etc.) without needing
        # `uv run` reentrancy.
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(
                f"rebuild-dashboard: {script.name} failed (exit {result.returncode})",
                file=sys.stderr,
            )
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode
        # Forward the script's own one-line summary so the user sees the
        # row count and output path.
        if result.stdout:
            print(result.stdout.rstrip())
    return 0


def _cmd_rebuild_dashboard(args: argparse.Namespace) -> None:
    repo_root = _find_repo_root()
    sys.exit(_rebuild_dashboard_data(repo_root))


def _cmd_publish(args: argparse.Namespace) -> None:
    repo_root = _find_repo_root()

    # Accept `source` both as an absolute path and as a path relative to the
    # user's cwd. If the cwd-relative form does not resolve, fall back to
    # repo-root-relative so `clispecbench publish transient_results/...`
    # works from subdirectories too.
    source = Path(args.source)
    if not source.is_absolute() and not source.is_file():
        repo_relative = repo_root / args.source
        if repo_relative.is_file():
            source = repo_relative
    if not source.is_file():
        print(f"publish: source not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    published_root = Path(args.published_dir)
    if not published_root.is_absolute():
        published_root = (repo_root / published_root).resolve()

    try:
        target = publish_result(
            source,
            published_root,
            status=args.status,
            last_message=args.last_message,
            commentary=args.commentary,
            force=args.force,
        )
    except PublishError as exc:
        print(f"publish: {exc}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"publish: source is not a valid result.json ({exc})", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"publish: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        rel = target.relative_to(repo_root)
        print(str(rel))
    except ValueError:
        print(str(target))

    if getattr(args, "rebuild_dashboard", False):
        rc = _rebuild_dashboard_data(repo_root)
        if rc != 0:
            sys.exit(rc)


def _cmd_validate(args: argparse.Namespace) -> None:
    repo_root = _find_repo_root()
    try:
        task = resolve_task(repo_root, args.task, language=getattr(args, "language", None))
    except (ValueError, FileNotFoundError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Task: {task.task_id}")
    print(f"Language: {task.language}")
    print(f"Root: {task.root}")
    print(f"Base prompt: {task.base_prompt_path}")
    print(f"Language prompt: {task.language_prompt_path}")
    print(f"Technical prompt: {task.technical_prompt_path}")
    print(f"Docs dir: {task.docs_dir}")
    print(f"Test dir: {task.test_dir}")
    print(f"Build script: {task.build_script or 'none'}")
    print(f"Prompt variants: {', '.join(sorted(task.prompt_variants)) or 'none'}")
    print("\nValidation passed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="clispecbench",
        description="CLISpecBench evaluation harness",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run an evaluation")
    run_parser.add_argument(
        "--task",
        required=True,
        help=(
            "Either a canonical '<eval>-<language>' task id (e.g. 'bibtex-cpp') "
            "or a bare eval name (e.g. 'bibtex') paired with --language. "
            f"Known evals: {', '.join(list_evals())}."
        ),
    )
    run_parser.add_argument(
        "--language",
        choices=list_languages(),
        default=None,
        help=(
            "Implementation language. Optional when --task already includes the "
            "language; required when --task is a bare eval name."
        ),
    )
    run_parser.add_argument(
        "--agent",
        required=True,
        choices=list_agent_ids(),
    )
    run_parser.add_argument("--runs", type=int, default=3)
    run_parser.add_argument("--prompt-variant", default=None)
    run_parser.add_argument("--output-dir", default="transient_results")
    run_parser.add_argument("--model", default=None, help="Model to use (e.g. opus, sonnet, o3)")
    run_parser.add_argument(
        "--effort",
        default=None,
        help="Effort / reasoning level (e.g. low, medium, high, max)",
    )
    run_parser.add_argument("--api-key-env", action="append", help="VAR=value pairs for API keys")
    run_parser.add_argument("--skip-extensions", action="store_true")

    # --- results ---
    results_parser = subparsers.add_parser("results", help="View evaluation results")
    results_parser.add_argument("--task", default=None)
    results_parser.add_argument("--agent", default=None)
    results_parser.add_argument("--output-dir", default="transient_results")
    results_parser.add_argument("--format", choices=["table", "json", "csv"], default="table")
    results_parser.add_argument("--compare", action="store_true")
    results_parser.add_argument(
        "--breakdown",
        action="store_true",
        help="Show per-capability subscore table instead of the default run table",
    )
    results_parser.add_argument(
        "--flakiness",
        action="store_true",
        help="Show tests whose outcomes aren't unanimous across repeated runs",
    )

    # --- backfill-subscores ---
    bf_parser = subparsers.add_parser(
        "backfill-subscores",
        help="Recompute per-capability subscores for existing result.json files",
    )
    bf_parser.add_argument("--output-dir", default="transient_results")
    bf_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing files",
    )
    bf_parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute subscores even if the file already has them",
    )

    # --- hash ---
    hash_parser = subparsers.add_parser(
        "hash",
        help="Print content hashes for a task's prompt + test suite",
    )
    hash_parser.add_argument("--task", required=True)
    hash_parser.add_argument("--language", choices=list_languages(), default=None)
    hash_parser.add_argument("--prompt-variant", default=None)
    hash_parser.add_argument(
        "--show-manifest",
        action="store_true",
        help="Also print the full per-file manifest that feeds each hash",
    )

    # --- publish ---
    publish_parser = subparsers.add_parser(
        "publish",
        help="Publish a transient result.json into published_results/",
    )
    publish_parser.add_argument(
        "source",
        help="Path to a transient result.json (e.g. transient_results/.../result.json)",
    )
    publish_parser.add_argument(
        "--status",
        required=True,
        help="Editorial status label (e.g. 'Complete', 'Incomplete', 'Context exhausted')",
    )
    publish_parser.add_argument(
        "--last-message",
        required=True,
        help="Editorial summary of the run's completion state (shown in results table)",
    )
    publish_parser.add_argument(
        "--commentary",
        default=None,
        help="Optional slug of a markdown file in published_results/<eval>/commentary/",
    )
    publish_parser.add_argument(
        "--published-dir",
        default=DEFAULT_PUBLISHED_DIR,
        help=f"Root of published_results tree (default: {DEFAULT_PUBLISHED_DIR}/)",
    )
    publish_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing publication sharing the same run_uid",
    )
    publish_parser.add_argument(
        "--rebuild-dashboard",
        action="store_true",
        help=(
            "After publishing, regenerate the dashboard's results-published.json "
            "and test-results-published.json so the new run shows up. Recommended "
            "for one-shot publishes; for batch publishes, omit this and run "
            "'clispecbench rebuild-dashboard' once at the end."
        ),
    )

    # --- rebuild-dashboard ---
    rebuild_parser = subparsers.add_parser(
        "rebuild-dashboard",
        help=(
            "Regenerate published_results/web/{results,test-results}-published.json "
            "from the current published_results/ tree."
        ),
    )
    # Reserved for future flags; argparse needs at least the subparser to dispatch.
    rebuild_parser.set_defaults(_subcommand="rebuild-dashboard")

    # --- validate ---
    validate_parser = subparsers.add_parser("validate", help="Validate a task definition")
    validate_parser.add_argument("--task", required=True)
    validate_parser.add_argument("--language", choices=list_languages(), default=None)

    args = parser.parse_args(argv)

    # Force line-buffered stdout/stderr so log lines are visible immediately
    # when the harness runs as a background task with output redirected to a
    # file.  Without this, Python's default block-buffering hides all output
    # until the process exits, making it impossible to tell whether a
    # multi-hour eval is alive or dead.
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    sys.stderr.reconfigure(line_buffering=True)  # type: ignore[attr-defined]

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "results":
        _cmd_results(args)
    elif args.command == "backfill-subscores":
        _cmd_backfill_subscores(args)
    elif args.command == "hash":
        _cmd_hash(args)
    elif args.command == "publish":
        _cmd_publish(args)
    elif args.command == "rebuild-dashboard":
        _cmd_rebuild_dashboard(args)
    elif args.command == "validate":
        _cmd_validate(args)


if __name__ == "__main__":
    main()
