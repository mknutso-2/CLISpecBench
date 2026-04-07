"""Tests for per-language task registration and prompt resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.harness.task import TaskDefinition, list_tasks, resolve_task


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


class TestTaskDefinitionLanguage:
    def test_definition_has_language_field(self) -> None:
        repo_root = _repo_root()
        task = resolve_task(repo_root, "wordcount")
        assert isinstance(task, TaskDefinition)
        assert task.language == "cpp"


class TestPythonTaskRegistration:
    def test_wordcount_python_is_registered(self) -> None:
        assert "wordcount-python" in list_tasks()

    def test_wordcount_python_resolves_to_python_language_prompt(self) -> None:
        repo_root = _repo_root()
        task = resolve_task(repo_root, "wordcount-python")

        assert task.language == "python"
        assert task.language_prompt_path.name == "language-requirements-python.md"
        assert task.language_prompt_path.is_file()
        # The technical prompt is shared across languages.
        assert task.technical_prompt_path.name == "technical-requirements-prompt.md"
        assert task.technical_prompt_path.is_file()

    def test_wordcount_python_shares_base_and_technical_with_cpp(self) -> None:
        repo_root = _repo_root()
        cpp = resolve_task(repo_root, "wordcount")
        py = resolve_task(repo_root, "wordcount-python")

        # Both share the same base prompt, technical prompt, and docs corpus.
        assert cpp.base_prompt_path == py.base_prompt_path
        assert cpp.technical_prompt_path == py.technical_prompt_path
        assert cpp.docs_dir == py.docs_dir
        # And the same hidden test directory.
        assert cpp.test_dir == py.test_dir
        # But different language prompts.
        assert cpp.language_prompt_path != py.language_prompt_path

    def test_unknown_task_raises(self) -> None:
        repo_root = _repo_root()
        with pytest.raises(ValueError, match="Unknown task"):
            resolve_task(repo_root, "wordcount-rust")
