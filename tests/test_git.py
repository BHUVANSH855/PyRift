"""
Tests for pyrift.git — Git helpers for changed-file scanning.
"""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from pyrift.git import GitError, changed_python_files, repository_root


class TestRepositoryRoot:
    def test_raises_git_error_when_not_in_repo(self, tmp_path):
        with (
            patch("subprocess.run", side_effect=subprocess.CalledProcessError(128, "git")),
            pytest.raises(GitError),
        ):
            repository_root(tmp_path)

    def test_raises_git_error_on_os_error(self, tmp_path):
        with (
            patch("subprocess.run", side_effect=OSError("git not found")),
            pytest.raises(GitError),
        ):
            repository_root(tmp_path)

    def test_returns_path_from_git_output(self, tmp_path):
        mock_result = MagicMock()
        mock_result.stdout = str(tmp_path) + "\n"
        with patch("subprocess.run", return_value=mock_result):
            result = repository_root(tmp_path)
        assert result == tmp_path.resolve()


class TestChangedPythonFiles:
    def test_raises_git_error_on_failure(self, tmp_path):
        with (
            patch("pyrift.git.repository_root", side_effect=GitError("no git")),
            pytest.raises(GitError),
        ):
            changed_python_files(tmp_path)

    def test_filters_non_python_files(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")

        with (
            patch("pyrift.git.repository_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout="test.py\nREADME.txt\n"),
                MagicMock(stdout=""),
                MagicMock(stdout=""),
            ]
            result = changed_python_files(tmp_path)

        assert all(p.suffix == ".py" for p in result)

    def test_returns_sorted_list(self, tmp_path):
        b_py = tmp_path / "b.py"
        a_py = tmp_path / "a.py"
        b_py.write_text("x = 1")
        a_py.write_text("x = 1")

        with (
            patch("pyrift.git.repository_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout="b.py\na.py\n"),
                MagicMock(stdout=""),
                MagicMock(stdout=""),
            ]
            result = changed_python_files(tmp_path)

        assert result == sorted(result)

    def test_excludes_files_outside_target_path(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        outside_file = tmp_path / "outside.py"
        outside_file.write_text("x = 1")
        inside_file = sub / "inside.py"
        inside_file.write_text("x = 1")

        with (
            patch("pyrift.git.repository_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout="outside.py\nsub/inside.py\n"),
                MagicMock(stdout=""),
                MagicMock(stdout=""),
            ]
            result = changed_python_files(sub)

        # Files outside the scan target (sub/) should be excluded
        # Result should only contain files under sub/
        for p in result:
            assert "inside.py" in str(p) or p.parent == sub

    def test_git_subprocess_error_raises_git_error(self, tmp_path):
        with (
            patch("pyrift.git.repository_root", return_value=tmp_path),
            patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")),
            pytest.raises(GitError),
        ):
            changed_python_files(tmp_path)

    def test_skips_deleted_files(self, tmp_path):
        existing = tmp_path / "exists.py"
        existing.write_text("x = 1")

        with (
            patch("pyrift.git.repository_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout="exists.py\ndeleted.py\n"),
                MagicMock(stdout=""),
                MagicMock(stdout=""),
            ]
            result = changed_python_files(tmp_path)

        assert all(p.exists() for p in result)

    def test_deduplicates_across_diff_and_staged(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")

        with (
            patch("pyrift.git.repository_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            # Same file in both diff and staged
            mock_run.side_effect = [
                MagicMock(stdout="test.py\n"),
                MagicMock(stdout="test.py\n"),
                MagicMock(stdout=""),
            ]
            result = changed_python_files(tmp_path)

        assert len(result) == 1