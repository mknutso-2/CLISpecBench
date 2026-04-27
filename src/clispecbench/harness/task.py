"""Task registry: discovers and loads CLISpecBench task definitions."""

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
    """A loaded CLISpecBench task ready for evaluation."""

    task_id: str
    root: Path
    base_prompt_path: Path
    language_prompt_path: Path
    technical_prompt_path: Path
    docs_dir: Path
    test_dir: Path
    language: str
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


def _language_prompt_path(task_root: Path, language: str) -> Path:
    """Locate the shared language-requirements prompt for *language*.

    Shared prompts live at ``Evals/_shared/language-requirements-<lang>.md``
    — i.e. a sibling of the task directory.
    """
    return task_root.parent / "_shared" / f"language-requirements-{language}.md"


def load_task(
    task_root: Path,
    task_id: str,
    *,
    language: str,
) -> TaskDefinition:
    """Load a task definition from the conventional directory layout.

    Expected structure under *task_root*::

        prompt/
          base-prompt.md
          technical-requirements-prompt.md           # shared across languages
          docs/
          variants/                                   (optional)
        tests/
        harness/
          build.sh           (optional)
        sample-tests/        (optional)
    """
    prompt_dir = task_root / "prompt"
    base_prompt = prompt_dir / "base-prompt.md"
    tech_prompt = prompt_dir / "technical-requirements-prompt.md"
    language_prompt = _language_prompt_path(task_root, language)
    docs_dir = prompt_dir / "docs"
    test_dir = task_root / "tests"

    if not base_prompt.is_file():
        raise FileNotFoundError(f"Base prompt not found: {base_prompt}")
    if not tech_prompt.is_file():
        raise FileNotFoundError(f"Technical prompt not found: {tech_prompt}")
    if not language_prompt.is_file():
        raise FileNotFoundError(f"Language prompt for {language!r} not found: {language_prompt}")
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
        language_prompt_path=language_prompt,
        technical_prompt_path=tech_prompt,
        docs_dir=docs_dir,
        test_dir=test_dir,
        language=language,
        version=version,
        build_script=build_script if build_script.is_file() else None,
        sample_test_dir=sample_test_dir if sample_test_dir.is_dir() else None,
        prompt_variants=_discover_prompt_variants(prompt_dir),
    )


# ---------------------------------------------------------------------------
# Eval registry — maps eval names to subdirs.
#
# Language is intentionally NOT part of the registry. Eval prompts and tests
# are language-agnostic (the agent writes the implementation; tests use the
# shared `submission_command` fixture). The available languages are determined
# by which ``Evals/_shared/language-requirements-<lang>.md`` files exist.
#
# Task IDs at the CLI continue to use ``<eval>-<language>`` form (e.g.
# ``bibtex-cpp``) so output paths and historical results keep their shape.
# ---------------------------------------------------------------------------


_KNOWN_EVALS: dict[str, str] = {
    "rs274": "Evals/RS274",
    # Historical alias for RS274 — kept for backwards compatibility with
    # earlier results and scripts.
    "cncsim": "Evals/RS274",
    "wordcount": "Evals/WordCount",
    "iges": "Evals/IGES",
    "bibtex": "Evals/BibTeX",
    "ical": "Evals/ICal",
    "gedcom": "Evals/GEDCOM",
    "las": "Evals/LAS",
    "marc21": "Evals/MARC21",
}


def list_evals() -> list[str]:
    """Return the sorted list of registered eval names (without languages)."""
    return sorted(_KNOWN_EVALS)


def list_languages() -> list[str]:
    """Return the sorted list of languages with a shared language-requirements file."""
    shared_dir = Path(__file__).resolve().parents[3] / "Evals" / "_shared"
    if not shared_dir.is_dir():
        return []
    languages: set[str] = set()
    for path in shared_dir.glob("language-requirements-*.md"):
        stem = path.stem  # language-requirements-<lang>
        prefix = "language-requirements-"
        if stem.startswith(prefix):
            languages.add(stem[len(prefix) :])
    return sorted(languages)


def split_task_id(task_id: str) -> tuple[str, str]:
    """Split a CLI ``<eval>-<language>`` task id into ``(eval_name, language)``.

    Raises ``ValueError`` on a malformed id.
    """
    if "-" not in task_id:
        raise ValueError(
            f"Task id {task_id!r} must use the form '<eval>-<language>' "
            f"(e.g. 'bibtex-cpp'). Known evals: {', '.join(list_evals())}."
        )
    eval_name, _, language = task_id.rpartition("-")
    return eval_name, language


def resolve_task(repo_root: Path, task_id: str, *, language: str | None = None) -> TaskDefinition:
    """Resolve a CLI task identifier to a loaded :class:`TaskDefinition`.

    Two calling forms are accepted:

    - ``resolve_task(root, "bibtex-cpp")`` — legacy/canonical form, language
      embedded in the id.
    - ``resolve_task(root, "bibtex", language="cpp")`` — preferred form, eval
      name and language as orthogonal arguments.

    The canonical task id stored on the result is always ``<eval>-<language>``.
    """
    if language is None:
        eval_name, language = split_task_id(task_id)
        canonical_id = task_id
    else:
        eval_name = task_id
        canonical_id = f"{eval_name}-{language}"
    subdir = _KNOWN_EVALS.get(eval_name)
    if subdir is None:
        raise ValueError(f"Unknown eval {eval_name!r}. Known evals: {', '.join(list_evals())}.")
    return load_task(
        repo_root / subdir,
        canonical_id,
        language=language,
    )


def list_tasks() -> list[str]:
    """Return the sorted list of canonical ``<eval>-<language>`` task ids.

    The cross product of every registered eval with every language that has
    a shared ``language-requirements-<lang>.md`` file. Used for argparse
    ``choices=`` lists; the runtime resolver does not enforce membership in
    this list.
    """
    return sorted(
        f"{eval_name}-{language}" for eval_name in _KNOWN_EVALS for language in list_languages()
    )
