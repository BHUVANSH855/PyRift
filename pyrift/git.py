"""
pyrift.git
~~~~~~~~~

Git helpers for maintainer-oriented changed-file scanning.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Raised when Git metadata cannot be read."""


def repository_root(path: str | Path) -> Path:
    """Return the Git repository root containing ``path``."""
    target = Path(path).resolve()
    cwd = target if target.is_dir() else target.parent

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitError("unable to determine Git repository root") from exc

    return Path(completed.stdout.strip()).resolve()


def changed_python_files(
    path: str | Path,
    base: str = "HEAD",
) -> list[Path]:
    """
    Return changed Python files under ``path``.

    The comparison includes both staged and unstaged working-tree changes
    relative to ``base``. Untracked Python files are also included because
    they are part of the developer's current working tree.
    """
    target = Path(path).resolve()
    root = repository_root(target)

    try:
        completed = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMRTUXB",
                base,
                "--",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

        staged = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "--cached",
                "--diff-filter=ACMRTUXB",
                "--",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

        untracked = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitError(
            f"unable to determine changed files relative to {base!r}"
        ) from exc

    candidates = set(
        completed.stdout.splitlines()
        + staged.stdout.splitlines()
        + untracked.stdout.splitlines()
    )

    changed: list[Path] = []

    for raw_path in candidates:
        relative = Path(raw_path)

        if relative.suffix.lower() != ".py":
            continue

        absolute = (root / relative).resolve()

        if not absolute.is_file():
            continue

        try:
            absolute.relative_to(target)
        except ValueError:
            continue

        changed.append(absolute)

    return sorted(changed)