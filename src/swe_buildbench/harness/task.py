"""Task registry: discovers and loads SWE-BuildBench task definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExtensionTask:
    """An extension task within a parent task."""

    extension_id: str
    prompt_path: Path
    test_dir: Path | None = None
    docs_dir: Path | None = None


@dataclass
class TaskDefinition:
    """A loaded SWE-BuildBench task ready for evaluation."""

    task_id: str
    root: Path
    base_prompt_path: Path
    technical_prompt_path: Path
    docs_dir: Path
    test_dir: Path
    version: str = "0.0.0"
    build_script: Path | None = None
    sample_test_dir: Path | None = None
    prompt_variants: dict[str, Path] = field(default_factory=dict[str, Path])
    extensions: list[ExtensionTask] = field(default_factory=list[ExtensionTask])


def _discover_prompt_variants(prompts_dir: Path) -> dict[str, Path]:
    variants_dir = prompts_dir / "variants"
    if not variants_dir.is_dir():
        return {}
    return {p.stem: p for p in sorted(variants_dir.glob("*.md"))}


def load_task(task_root: Path, task_id: str) -> TaskDefinition:
    """Load a task definition from the conventional directory layout.

    Expected structure under *task_root*::

        prompt/
          base-prompt.md
          technical-requirements-prompt.md
          docs/
          variants/          (optional)
        tests/
        harness/
          build.sh           (optional)
        sample-tests/        (optional)
    """
    prompt_dir = task_root / "prompt"
    base_prompt = prompt_dir / "base-prompt.md"
    tech_prompt = prompt_dir / "technical-requirements-prompt.md"
    docs_dir = prompt_dir / "docs"
    test_dir = task_root / "tests"

    if not base_prompt.is_file():
        raise FileNotFoundError(f"Base prompt not found: {base_prompt}")
    if not tech_prompt.is_file():
        raise FileNotFoundError(f"Technical prompt not found: {tech_prompt}")
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")
    if not test_dir.is_dir():
        raise FileNotFoundError(f"Test directory not found: {test_dir}")

    build_script = task_root / "harness" / "build.sh"
    sample_test_dir = task_root / "sample-tests"

    version_file = task_root / "VERSION"
    version = version_file.read_text().strip() if version_file.is_file() else "0.0.0"

    return TaskDefinition(
        task_id=task_id,
        root=task_root,
        base_prompt_path=base_prompt,
        technical_prompt_path=tech_prompt,
        docs_dir=docs_dir,
        test_dir=test_dir,
        version=version,
        build_script=build_script if build_script.is_file() else None,
        sample_test_dir=sample_test_dir if sample_test_dir.is_dir() else None,
        prompt_variants=_discover_prompt_variants(prompt_dir),
    )


# ---------------------------------------------------------------------------
# Task registry — maps task IDs to loader callables
# ---------------------------------------------------------------------------

_KNOWN_TASKS: dict[str, str] = {
    "cncsim-full": "Evals/CNCSim",
    "cncsim-lite": "Evals/CNCSim",
    "wordcount": "Evals/WordCount",
}


def resolve_task(repo_root: Path, task_id: str) -> TaskDefinition:
    """Resolve a task ID to a loaded :class:`TaskDefinition`.

    Raises ``ValueError`` if the task ID is not recognised.
    """
    subdir = _KNOWN_TASKS.get(task_id)
    if subdir is None:
        known = ", ".join(sorted(_KNOWN_TASKS))
        raise ValueError(f"Unknown task {task_id!r}. Known tasks: {known}")
    return load_task(repo_root / subdir, task_id)


def list_tasks() -> list[str]:
    """Return sorted list of known task IDs."""
    return sorted(_KNOWN_TASKS)
