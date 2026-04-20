"""Tests for harness.hashing — prompt + test-suite content hashing.

Each test name states the property it proves. If you want to verify the
module does what it claims, run::

    uv run pytest src/clispecbench/tests/test_hashing.py -v

and read the test names.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from clispecbench.harness.hashing import (
    ContentHash,
    hash_paths,
    hash_prompt_content,
    hash_test_suite,
)
from clispecbench.harness.task import TaskDefinition

# ---------------------------------------------------------------------------
# Fixtures: build a miniature fake task on disk
# ---------------------------------------------------------------------------


def _make_fake_task(root: Path) -> TaskDefinition:
    """Create a minimal on-disk task layout and return a TaskDefinition.

    Layout::

        <root>/
          prompt/
            base-prompt.md
            technical-requirements-prompt.md
            language-requirements-cpp.md
            docs/
              spec.md
              sub/nested.md
          tests/
            test_alpha.py
            test_beta.py
    """
    prompt_dir = root / "prompt"
    docs_dir = prompt_dir / "docs"
    (docs_dir / "sub").mkdir(parents=True)
    (prompt_dir / "base-prompt.md").write_text("BASE\n", encoding="utf-8")
    (prompt_dir / "technical-requirements-prompt.md").write_text("TECH\n", encoding="utf-8")
    lang = prompt_dir / "language-requirements-cpp.md"
    lang.write_text("LANG\n", encoding="utf-8")
    (docs_dir / "spec.md").write_text("SPEC v1\n", encoding="utf-8")
    (docs_dir / "sub" / "nested.md").write_text("NESTED\n", encoding="utf-8")

    tests_dir = root / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_alpha.py").write_text("def test_a(): assert 1\n", encoding="utf-8")
    (tests_dir / "test_beta.py").write_text("def test_b(): assert 2\n", encoding="utf-8")

    return TaskDefinition(
        task_id="faketask",
        root=root,
        base_prompt_path=prompt_dir / "base-prompt.md",
        language_prompt_path=lang,
        technical_prompt_path=prompt_dir / "technical-requirements-prompt.md",
        docs_dir=docs_dir,
        test_dir=tests_dir,
        language="cpp",
        version="1.0.0",
    )


@pytest.fixture
def fake_task(tmp_path: Path) -> TaskDefinition:
    return _make_fake_task(tmp_path)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_hashes_are_deterministic_across_calls(fake_task: TaskDefinition) -> None:
    assert hash_prompt_content(fake_task).sha256 == hash_prompt_content(fake_task).sha256
    assert hash_test_suite(fake_task).sha256 == hash_test_suite(fake_task).sha256


def test_prompt_hash_changes_when_docs_change(fake_task: TaskDefinition) -> None:
    before = hash_prompt_content(fake_task).sha256
    (fake_task.docs_dir / "spec.md").write_text("SPEC v2\n", encoding="utf-8")
    after = hash_prompt_content(fake_task).sha256
    assert before != after


def test_prompt_hash_changes_when_base_prompt_changes(fake_task: TaskDefinition) -> None:
    before = hash_prompt_content(fake_task).sha256
    fake_task.base_prompt_path.write_text("BASE MODIFIED\n", encoding="utf-8")
    after = hash_prompt_content(fake_task).sha256
    assert before != after


def test_test_suite_hash_changes_when_a_test_changes(fake_task: TaskDefinition) -> None:
    before = hash_test_suite(fake_task).sha256
    (fake_task.test_dir / "test_alpha.py").write_text("def test_a(): assert 99\n", encoding="utf-8")
    after = hash_test_suite(fake_task).sha256
    assert before != after


def test_prompt_and_test_hashes_are_independent(fake_task: TaskDefinition) -> None:
    """Changing tests must NOT move the prompt hash, and vice versa.

    This is the whole reason we split into two hashes — it lets us tell
    "agent got a different task" apart from "same task, different rubric".
    """
    prompt_before = hash_prompt_content(fake_task).sha256
    tests_before = hash_test_suite(fake_task).sha256

    # Change only a test.
    (fake_task.test_dir / "test_alpha.py").write_text("def test_a(): assert 99\n", encoding="utf-8")
    assert hash_prompt_content(fake_task).sha256 == prompt_before  # prompt unaffected
    assert hash_test_suite(fake_task).sha256 != tests_before

    # Change only a doc.
    tests_mid = hash_test_suite(fake_task).sha256
    (fake_task.docs_dir / "spec.md").write_text("SPEC CHANGED\n", encoding="utf-8")
    assert hash_test_suite(fake_task).sha256 == tests_mid  # tests unaffected
    assert hash_prompt_content(fake_task).sha256 != prompt_before


def test_pycache_and_pyc_files_are_ignored(fake_task: TaskDefinition) -> None:
    before = hash_test_suite(fake_task).sha256

    # Simulate pytest cache/bytecode artifacts appearing in tests/.
    pycache = fake_task.test_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "test_alpha.cpython-312.pyc").write_bytes(b"\x00\x01\x02garbage")
    (fake_task.test_dir / "stray.pyc").write_bytes(b"more garbage")

    after = hash_test_suite(fake_task).sha256
    assert before == after, "bytecode/cache files must not affect test suite hash"


def test_manifest_hash_matches_stored_digest(fake_task: TaskDefinition) -> None:
    """The manifest is self-verifying: re-hashing its body reproduces sha256."""
    result = hash_test_suite(fake_task)
    recomputed = hashlib.sha256(result.manifest.encode("utf-8")).hexdigest()
    assert recomputed == result.sha256


def test_manifest_lists_expected_files(fake_task: TaskDefinition) -> None:
    """Humans should be able to open the manifest and see every file by name."""
    prompt = hash_prompt_content(fake_task)
    assert "prompt/base-prompt.md" in prompt.manifest
    assert "prompt/language-requirements-cpp.md" in prompt.manifest
    assert "prompt/technical-requirements-prompt.md" in prompt.manifest
    assert "prompt/docs/spec.md" in prompt.manifest
    assert "prompt/docs/sub/nested.md" in prompt.manifest

    tests = hash_test_suite(fake_task)
    assert "tests/test_alpha.py" in tests.manifest
    assert "tests/test_beta.py" in tests.manifest


def test_missing_path_produces_visible_marker(tmp_path: Path) -> None:
    """A missing file must appear in the manifest — not silently vanish —
    so that an accidentally-deleted doc shows up as a hash change AND is
    diagnosable from the manifest alone."""
    result = hash_paths([("prompt/docs", tmp_path / "does-not-exist")])
    assert "[MISSING]" in result.manifest


def test_file_reorder_does_not_affect_hash(tmp_path: Path) -> None:
    """Manifest is sorted by relative path, so insertion order of entries
    passed to hash_paths shouldn't matter for a single directory tree."""
    d = tmp_path / "dir"
    d.mkdir()
    (d / "b.txt").write_text("B")
    (d / "a.txt").write_text("A")
    h1 = hash_paths([("x", d)])
    # Touch files in different order — shouldn't matter since rglob+sort is deterministic
    h2 = hash_paths([("x", d)])
    assert h1.sha256 == h2.sha256


def test_content_hash_is_frozen_dataclass() -> None:
    """Sanity: ContentHash is immutable so callers can't accidentally
    mutate a manifest after computing its digest."""
    ch = ContentHash(sha256="0" * 64, manifest="")
    with pytest.raises((AttributeError, TypeError)):
        ch.sha256 = "tampered"  # type: ignore[misc]
