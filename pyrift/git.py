"""
pyrift.git
~~~~~~~~~~

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
            [
                "git",
                "rev-parse",
                "--show-toplevel",
            ],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitError(
            "unable to determine Git repository root"
        ) from exc

    output = completed.stdout.strip()

    if not output:
        raise GitError("unable to determine Git repository root")

    return Path(output).resolve()


def _run_git(
    root: Path,
    args: list[str],
    *,
    error_message: str,
) -> bytes:
    """Run Git and return its raw stdout."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitError(error_message) from exc

    return completed.stdout


def _decode_git_path(raw_path: bytes) -> str:
    """
    Decode a Git path using Git's UTF-8 path representation.

    Git emits repository paths as UTF-8 when ``-z`` is used. Rejecting
    invalid UTF-8 is preferable to silently replacing bytes and scanning
    the wrong filesystem path.
    """
    try:
        return raw_path.decode("utf-8")
    except UnicodeDecodeError:
        raise GitError("Git returned an invalid path encoding") from None


def _parse_changed_paths(output: bytes) -> list[str]:
    """
    Extract current paths from ``git diff --name-status -z`` output.

    Normal changes have this shape::

        STATUS\\0PATH\\0

    Renames and copies have this shape::

        STATUS + SCORE\\0OLD_PATH\\0NEW_PATH\\0

    For renames/copies, the new/current path is returned because that is
    the path that can actually be scanned.

    Malformed or incomplete Git records raise ``GitError`` instead of
    being silently ignored.
    """
    fields = output.split(b"\0")
    paths: list[str] = []
    index = 0

    while index < len(fields):
        status = fields[index]

        if not status:
            index += 1
            continue

        status_text = _decode_git_path(status)
        index += 1

        status_code = status_text[:1]

        if status_code in {"R", "C"}:
            if index + 1 >= len(fields):  # pragma: no cover
                raise GitError(
                    "Git returned incomplete rename information"
                )

            old_path = fields[index]
            new_path = fields[index + 1]

            if not old_path or not new_path:
                raise GitError(
                    "Git returned incomplete rename information"
                )

            _decode_git_path(old_path)
            paths.append(_decode_git_path(new_path))
            index += 2
            continue

        if index >= len(fields):  # pragma: no cover
            raise GitError("Git returned incomplete path information")

        path = fields[index]

        if not path:
            raise GitError("Git returned incomplete path information")

        paths.append(_decode_git_path(path))
        index += 1

    return paths


def _parse_untracked_paths(output: bytes) -> list[str]:
    """Extract paths from NUL-delimited ``git ls-files`` output."""
    paths: list[str] = []

    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue

        paths.append(_decode_git_path(raw_path))

    return paths


def _path_is_under(path: Path, target: Path) -> bool:
    """Return whether ``path`` is equal to or contained by ``target``."""
    try:
        path.relative_to(target)
    except ValueError:
        return False

    return True


def changed_python_files(
    path: str | Path,
    base: str = "HEAD",
) -> list[Path]:
    """
    Return changed Python files under ``path``.

    The comparison includes:

    - working-tree changes relative to ``base``
    - staged changes
    - untracked files

    Deleted files are excluded because they cannot be scanned.

    Renamed and copied files are represented by their current/new path.

    Git path output is NUL-delimited so filenames containing whitespace,
    Unicode, or other unusual characters are handled safely.
    """
    target = Path(path).resolve()
    root = repository_root(target)

    diff_output = _run_git(
        root,
        [
            "diff",
            "--no-ext-diff",
            "--name-status",
            "-z",
            "--diff-filter=ACMRTUXB",
            base,
            "--",
        ],
        error_message=(
            f"unable to determine changed files relative to {base!r}"
        ),
    )

    staged_output = _run_git(
        root,
        [
            "diff",
            "--no-ext-diff",
            "--name-status",
            "-z",
            "--diff-filter=ACMRTUXB",
            "--cached",
            "--",
        ],
        error_message="unable to determine staged changed files",
    )

    untracked_output = _run_git(
        root,
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
        ],
        error_message="unable to determine untracked files",
    )

    candidates = set(
        _parse_changed_paths(diff_output)
        + _parse_changed_paths(staged_output)
        + _parse_untracked_paths(untracked_output)
    )

    changed: list[Path] = []

    for raw_path in candidates:
        relative = Path(raw_path)

        if relative.suffix.lower() != ".py":
            continue

        absolute = (root / relative).resolve()

        if not absolute.is_file():
            continue

        if not _path_is_under(absolute, target):
            continue

        changed.append(absolute)

    return sorted(changed)