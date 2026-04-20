"""Content hashing for prompt + test-suite reproducibility tracking.

Two questions this module answers for a given run:

1. ``prompt_content_sha`` — "did the agent actually see the prompt/docs I think
   it saw?" Covers the assembled prompt pieces (base/variant, language prompt,
   technical requirements) and every file under ``docs/``.

2. ``test_suite_sha`` — "is this run being scored against the rubric I think
   it is?" Covers every file under ``tests/``.

Both hashes are computed by building a *manifest* — a sorted list of
``<per-file-sha256>  <relative-path>`` lines — and hashing the manifest text.
The manifest itself is written alongside ``result.json`` so a human can open
it and see exactly which files contributed to each hash. That is the
"observability" property: the hash is not an opaque number, it is a
reproducible summary of a file list you can eyeball.

These are deliberately *in addition to* the manual ``eval_version`` /
``CHANGELOG.md`` bump rule — the manual bump is the human-facing semver, and
these hashes are the machine-checkable backstop that catches silent drift.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from clispecbench.harness.task import TaskDefinition

# Path components / suffixes that should never affect a content hash.
_IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache"}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}


@dataclass(frozen=True)
class ContentHash:
    """Result of hashing a set of files.

    Attributes:
        sha256: Hex digest of the manifest text.
        manifest: One line per file: ``"<per-file-sha256>  <relative-path>\n"``.
            Sorted by relative path. Hashing ``manifest.encode("utf-8")``
            reproduces ``sha256`` exactly.
    """

    sha256: str
    manifest: str


def _is_ignored(path: Path) -> bool:
    if path.suffix in _IGNORED_SUFFIXES:
        return True
    return any(part in _IGNORED_DIR_NAMES for part in path.parts)


def _iter_files(root: Path) -> list[Path]:
    """Return all non-ignored files under *root*, sorted by relative path."""
    if not root.exists():
        return []
    if root.is_file():
        return [] if _is_ignored(root) else [root]
    return sorted(
        (p for p in root.rglob("*") if p.is_file() and not _is_ignored(p.relative_to(root))),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_paths(entries: list[tuple[str, Path]]) -> ContentHash:
    """Hash a list of ``(logical-name, filesystem-path)`` entries.

    For each entry, every file under *path* (recursive, minus ignored files)
    is hashed and added to the manifest under ``<logical-name>/<relpath>``.
    Single-file entries appear as just ``<logical-name>``.
    """
    lines: list[str] = []
    for logical_name, fs_path in entries:
        if not fs_path.exists():
            # Record absence explicitly so a missing file is visible in the
            # manifest rather than silently producing the same hash as "file
            # exists but is empty".
            lines.append(f"{'0' * 64}  {logical_name}  [MISSING]\n")
            continue
        if fs_path.is_file():
            lines.append(f"{_hash_file(fs_path)}  {logical_name}\n")
            continue
        files = _iter_files(fs_path)
        if not files:
            lines.append(f"{'0' * 64}  {logical_name}/  [EMPTY]\n")
            continue
        for f in files:
            rel = f.relative_to(fs_path).as_posix()
            lines.append(f"{_hash_file(f)}  {logical_name}/{rel}\n")

    manifest = "".join(lines)
    sha = hashlib.sha256(manifest.encode("utf-8")).hexdigest()
    return ContentHash(sha256=sha, manifest=manifest)


def hash_prompt_content(task: TaskDefinition, variant: str | None = None) -> ContentHash:
    """Hash everything that shapes what the agent sees at prompt time."""
    if variant is not None:
        prompt_path = task.prompt_variants.get(variant, task.base_prompt_path)
        prompt_label = f"prompt/variants/{variant}.md"
    else:
        prompt_path = task.base_prompt_path
        prompt_label = "prompt/base-prompt.md"

    entries: list[tuple[str, Path]] = [
        (prompt_label, prompt_path),
        (
            f"prompt/language-requirements-{task.language}.md",
            task.language_prompt_path,
        ),
        ("prompt/technical-requirements-prompt.md", task.technical_prompt_path),
        ("prompt/docs", task.docs_dir),
    ]

    # Shared prompt fragments appended by assemble_prompt
    from clispecbench.harness.workspace import SHARED_PROMPTS_DIR

    one_shot = SHARED_PROMPTS_DIR / "require-one-shot.md"
    if one_shot.is_file():
        entries.append(("_shared/require-one-shot.md", one_shot))

    return hash_paths(entries)


def hash_test_suite(task: TaskDefinition) -> ContentHash:
    """Hash every file under the task's ``tests/`` directory."""
    return hash_paths([("tests", task.test_dir)])


def write_manifest(path: Path, content: ContentHash) -> None:
    """Write a manifest sidecar that reproduces ``content.sha256`` when hashed.

    Format:
        ``# sha256: <digest>\n``
        ``<per-file-sha256>  <relative-path>\n`` * N

    The header line starts with ``#`` so it is obviously not part of the
    hashed payload; tools (or humans) can strip the first line and re-hash
    the rest to verify.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"# sha256: {content.sha256}\n"
    path.write_text(header + content.manifest, encoding="utf-8")
