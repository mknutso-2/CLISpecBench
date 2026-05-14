"""Prepare the clean working directory that gets mounted into the agent container."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from clispecbench.harness.task import TaskDefinition

SHARED_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "Evals" / "_shared"


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

    parts = [
        base_text.rstrip(),
        language_text.strip(),
        tech_text.lstrip(),
    ]

    one_shot = SHARED_PROMPTS_DIR / "require-one-shot.md"
    if one_shot.is_file():
        parts.append(one_shot.read_text(encoding="utf-8").strip())

    return "\n\n".join(parts)


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
    workspace = Path(tempfile.mkdtemp(prefix="clispecbench-", dir=parent_dir))

    # Write assembled prompt
    prompt_text = assemble_prompt(task, variant)
    (workspace / "prompt.md").write_text(prompt_text, encoding="utf-8")

    # Copy documentation corpus
    shutil.copytree(task.docs_dir, workspace / "docs")

    return workspace
