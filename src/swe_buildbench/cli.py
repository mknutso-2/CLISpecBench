"""CLI entry point for swe-buildbench."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from swe_buildbench.agents.base import AgentAdapter
from swe_buildbench.harness.results import RunResult, load_result, next_run_number
from swe_buildbench.harness.runner import run_evaluation
from swe_buildbench.harness.task import list_tasks, resolve_task


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
    from collections.abc import Callable

    from swe_buildbench.agents import claude_code, codex_cli, gemini_cli, model_api

    adapters: dict[str, Callable[[], AgentAdapter]] = {
        "claude-code": lambda: claude_code.ClaudeCodeAdapter(
            model=model, effort=effort,
        ),
        "codex-cli": lambda: codex_cli.CodexCLIAdapter(
            model=model, effort=effort,
        ),
        "gemini-cli": lambda: gemini_cli.GeminiCLIAdapter(
            model=model, effort=effort,
        ),
        "model-api": lambda: model_api.ModelAPIAdapter(
            model=model or "claude-opus-4-6",
        ),
    }
    factory = adapters.get(agent_name)
    if factory is None:
        available = ", ".join(sorted(adapters))
        print(f"Unknown agent {agent_name!r}. Available: {available}", file=sys.stderr)
        sys.exit(1)
    return factory()


# ---------------------------------------------------------------------------
# Subcommand: run
# ---------------------------------------------------------------------------


def _cmd_run(args: argparse.Namespace) -> None:
    repo_root = _find_repo_root()
    task = resolve_task(repo_root, args.task)
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
    start_run = next_run_number(
        output_dir, task.task_id, adapter.name,
        adapter.model, adapter.effort,
    )
    if start_run > 1:
        logging.getLogger(__name__).info(
            "Found existing runs; starting at run%d", start_run,
        )
    for i in range(num_runs):
        run_number = start_run + i
        print(f"\n{'='*60}")
        print(f"Run {run_number} ({i+1}/{num_runs}): {args.task} / {adapter.name}")
        print(f"{'='*60}\n")

        result = run_evaluation(
            task=task,
            adapter=adapter,
            run_number=run_number,
            prompt_variant=args.prompt_variant,
            timeout_seconds=args.timeout,
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


# ---------------------------------------------------------------------------
# Subcommand: results
# ---------------------------------------------------------------------------


def _cmd_results(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    if not output_dir.is_dir():
        print(f"No results directory found at {output_dir}", file=sys.stderr)
        sys.exit(1)

    # Collect all result files matching filters
    results: list[RunResult] = []
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
        results.append(r)

    if not results:
        print("No matching results found.")
        return

    # Print table
    print(f"{'Task':<20} {'Agent':<15} {'Run':<5} {'Pass':<6} {'Total':<6} "
          f"{'Score':<8} {'Tokens':<10} {'Exit':<10}")
    print("-" * 90)
    for r in results:
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


def _cmd_validate(args: argparse.Namespace) -> None:
    repo_root = _find_repo_root()
    try:
        task = resolve_task(repo_root, args.task)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Task: {task.task_id}")
    print(f"Root: {task.root}")
    print(f"Base prompt: {task.base_prompt_path}")
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
        prog="swe-buildbench",
        description="SWE-BuildBench evaluation harness",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run an evaluation")
    run_parser.add_argument("--task", required=True, choices=list_tasks())
    run_parser.add_argument(
        "--agent",
        required=True,
        choices=["claude-code", "codex-cli", "gemini-cli", "model-api"],
    )
    run_parser.add_argument("--runs", type=int, default=3)
    run_parser.add_argument("--prompt-variant", default=None)
    run_parser.add_argument("--timeout", type=float, default=30 * 60)
    run_parser.add_argument("--output-dir", default="results")
    run_parser.add_argument("--model", default=None, help="Model to use (e.g. opus, sonnet, o3)")
    run_parser.add_argument(
        "--effort", default=None,
        help="Effort / reasoning level (e.g. low, medium, high, max)",
    )
    run_parser.add_argument(
        "--api-key-env", action="append", help="VAR=value pairs for API keys"
    )
    run_parser.add_argument("--skip-extensions", action="store_true")

    # --- results ---
    results_parser = subparsers.add_parser("results", help="View evaluation results")
    results_parser.add_argument("--task", default=None)
    results_parser.add_argument("--agent", default=None)
    results_parser.add_argument("--output-dir", default="results")
    results_parser.add_argument(
        "--format", choices=["table", "json", "csv"], default="table"
    )
    results_parser.add_argument("--compare", action="store_true")

    # --- validate ---
    validate_parser = subparsers.add_parser("validate", help="Validate a task definition")
    validate_parser.add_argument("--task", required=True, choices=list_tasks())

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "results":
        _cmd_results(args)
    elif args.command == "validate":
        _cmd_validate(args)


if __name__ == "__main__":
    main()
