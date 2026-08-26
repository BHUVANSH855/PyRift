"""
End-to-end coverage for changed-only scanning.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from pyrift.git import changed_python_files


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def test_changed_only_selects_only_changed_python_files(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "PyRift Tests")

    unchanged = repo / "unchanged.py"
    changed = repo / "changed.py"

    unchanged.write_text("value = 1\n", encoding="utf-8")
    changed.write_text("value = 1\n", encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    changed.write_text("value = 2\n", encoding="utf-8")

    new_file = repo / "new.py"
    new_file.write_text("value = 3\n", encoding="utf-8")

    files = changed_python_files(repo)

    assert files == [
        changed.resolve(),
        new_file.resolve(),
    ]
    assert unchanged.resolve() not in files