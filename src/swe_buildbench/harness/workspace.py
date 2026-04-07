"""Prepare the clean working directory that gets mounted into the agent container."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from swe_buildbench.harness.task import TaskDefinition


def assemble_prompt(task: TaskDefinition, variant: str | None = None) -> str:
    """Concatenate the base prompt (or variant) with the technical requirements."""
    if variant is not None:
        prompt_path = task.prompt_variants.get(variant)
        if prompt_path is None:
            available = ", ".join(sorted(task.prompt_variants)) or "(none)"
            raise ValueError(
                f"Unknown prompt variant {variant!r} for task {task.task_id}. "
                f"Available: {available}"
            )
    else:
        prompt_path = task.base_prompt_path

    base_text = prompt_path.read_text(encoding="utf-8")
    language_text = task.language_prompt_path.read_text(encoding="utf-8")
    tech_text = task.technical_prompt_path.read_text(encoding="utf-8")
    return (
        base_text.rstrip()
        + "\n\n"
        + language_text.strip()
        + "\n\n"
        + tech_text.lstrip()
    )


def prepare_workspace(
    task: TaskDefinition,
    variant: str | None = None,
    parent_dir: Path | None = None,
) -> Path:
    """Create a temporary workspace directory for an agent run.

    Layout inside the returned directory::

        prompt.md          # Assembled prompt (base + technical)
        docs/              # Copy of the documentation corpus

    The caller is responsible for cleaning up the returned directory
    (e.g. via :func:`shutil.rmtree`).
    """
    workspace = Path(tempfile.mkdtemp(prefix="swe-bb-", dir=parent_dir))

    # Write assembled prompt
    prompt_text = assemble_prompt(task, variant)
    (workspace / "prompt.md").write_text(prompt_text, encoding="utf-8")

    # Copy documentation corpus
    shutil.copytree(task.docs_dir, workspace / "docs")

    return workspace
