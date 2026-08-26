"""
Tests for Git changed-file discovery.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pyrift.git import GitError, changed_python_files, repository_root


def _git(
    repo: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "PyRift Tests")

    return repo


def test_repository_root_returns_repo_root(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    nested = repo / "src"
    nested.mkdir()

    assert repository_root(nested) == repo.resolve()


def test_changed_python_files_returns_modified_python_files(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)

    source = repo / "example.py"
    source.write_text("value = 1\n", encoding="utf-8")

    readme = repo / "README.md"
    readme.write_text("# Example\n", encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    source.write_text("value = 2\n", encoding="utf-8")
    readme.write_text("# Updated\n", encoding="utf-8")

    assert changed_python_files(repo) == [source.resolve()]


def test_changed_python_files_includes_new_python_files(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)

    initial = repo / "initial.py"
    initial.write_text("value = 1\n", encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    new_file = repo / "new_module.py"
    new_file.write_text("value = 2\n", encoding="utf-8")

    assert changed_python_files(repo) == [new_file.resolve()]


def test_changed_python_files_includes_staged_new_python_files(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)

    initial = repo / "initial.py"
    initial.write_text("value = 1\n", encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    new_file = repo / "staged_module.py"
    new_file.write_text("value = 2\n", encoding="utf-8")

    _git(repo, "add", str(new_file))

    assert changed_python_files(repo) == [new_file.resolve()]


def test_changed_python_files_excludes_non_python_files(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)

    source = repo / "example.py"
    source.write_text("value = 1\n", encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    readme = repo / "README.md"
    readme.write_text("# Updated\n", encoding="utf-8")

    assert changed_python_files(repo) == []


def test_changed_python_files_respects_path_scope(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)

    src = repo / "src"
    src.mkdir()

    inside = src / "inside.py"
    inside.write_text("value = 1\n", encoding="utf-8")

    outside = repo / "outside.py"
    outside.write_text("value = 1\n", encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    inside.write_text("value = 2\n", encoding="utf-8")
    outside.write_text("value = 2\n", encoding="utf-8")

    assert changed_python_files(src) == [inside.resolve()]


def test_changed_python_files_raises_for_non_git_directory(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "not-a-repo"
    directory.mkdir()

    with pytest.raises(GitError):
        changed_python_files(directory)