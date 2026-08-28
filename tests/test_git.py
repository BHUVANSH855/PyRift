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
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(128, "git"),
            ),
            pytest.raises(GitError),
        ):
            repository_root(tmp_path)

    def test_raises_git_error_on_os_error(self, tmp_path):
        with (
            patch(
                "subprocess.run",
                side_effect=OSError("git not found"),
            ),
            pytest.raises(GitError),
        ):
            repository_root(tmp_path)

    def test_returns_path_from_git_output(self, tmp_path):
        mock_result = MagicMock()
        mock_result.stdout = str(tmp_path) + "\n"

        with patch("subprocess.run", return_value=mock_result):
            result = repository_root(tmp_path)

        assert result == tmp_path.resolve()

    def test_raises_git_error_when_output_is_empty(self, tmp_path):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with (
            patch(
                "subprocess.run",
                return_value=mock_result,
            ),
            pytest.raises(GitError),
        ):
            repository_root(tmp_path)


class TestChangedPythonFiles:
    def test_raises_git_error_when_repository_root_fails(
        self,
        tmp_path,
    ):
        with (
            patch(
                "pyrift.git.repository_root",
                side_effect=GitError("no git"),
            ),
            pytest.raises(GitError),
        ):
            changed_python_files(tmp_path)

    def test_filters_non_python_files(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0test.py\0"),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [py_file.resolve()]

    def test_returns_sorted_list(self, tmp_path):
        b_py = tmp_path / "b.py"
        a_py = tmp_path / "a.py"

        b_py.write_text("x = 1", encoding="utf-8")
        a_py.write_text("x = 1", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=b"M\0b.py\0M\0a.py\0",
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [
            a_py.resolve(),
            b_py.resolve(),
        ]

    def test_excludes_files_outside_target_path(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()

        outside_file = tmp_path / "outside.py"
        outside_file.write_text("x = 1", encoding="utf-8")

        inside_file = sub / "inside.py"
        inside_file.write_text("x = 1", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=(
                        b"M\0outside.py\0"
                        b"M\0sub/inside.py\0"
                    ),
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(sub)

        assert result == [inside_file.resolve()]
        assert outside_file.resolve() not in result

    def test_git_subprocess_error_raises_git_error(self, tmp_path):
        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(
                    1,
                    "git",
                ),
            ),
            pytest.raises(GitError),
        ):
            changed_python_files(tmp_path)

    def test_skips_deleted_files(self, tmp_path):
        existing = tmp_path / "exists.py"
        existing.write_text("x = 1", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=b"D\0deleted.py\0M\0exists.py\0",
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [existing.resolve()]

    def test_deduplicates_across_diff_and_staged(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0test.py\0"),
                MagicMock(stdout=b"M\0test.py\0"),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [py_file.resolve()]

    def test_includes_untracked_python_files(self, tmp_path):
        new_file = tmp_path / "new_module.py"
        new_file.write_text("value = 2\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
                MagicMock(stdout=b"new_module.py\0"),
            ]

            result = changed_python_files(tmp_path)

        assert result == [new_file.resolve()]

    def test_ignores_untracked_non_python_files(self, tmp_path):
        new_file = tmp_path / "README.md"
        new_file.write_text("hello\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
                MagicMock(stdout=b"README.md\0"),
            ]

            result = changed_python_files(tmp_path)

        assert result == []

    def test_handles_paths_with_spaces(self, tmp_path):
        py_file = tmp_path / "module with spaces.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=b"M\0module with spaces.py\0",
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [py_file.resolve()]

    def test_handles_renamed_python_file(self, tmp_path):
        new_file = tmp_path / "new_name.py"
        new_file.write_text("x = 1\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=(
                        b"R100\0old_name.py\0"
                        b"new_name.py\0"
                    ),
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [new_file.resolve()]

    def test_handles_copied_python_file(self, tmp_path):
        copied_file = tmp_path / "copied.py"
        copied_file.write_text("x = 1\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=(
                        b"C100\0original.py\0"
                        b"copied.py\0"
                    ),
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [copied_file.resolve()]

    def test_ignores_renamed_file_when_new_path_is_not_python(
        self,
        tmp_path,
    ):
        new_file = tmp_path / "README.md"
        new_file.write_text("hello\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=(
                        b"R100\0old_name.py\0"
                        b"README.md\0"
                    ),
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == []

    def test_raises_for_incomplete_rename_record(self, tmp_path):
        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=b"R100\0old_name.py\0",
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            with pytest.raises(GitError, match="incomplete rename"):
                changed_python_files(tmp_path)

    def test_raises_for_incomplete_normal_record(self, tmp_path):
        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0"),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            with pytest.raises(
                GitError,
                match="incomplete path information",
            ):
                changed_python_files(tmp_path)

    def test_raises_for_empty_rename_path(self, tmp_path):
        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(
                    stdout=b"R100\0old_name.py\0\0",
                ),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            with pytest.raises(
                GitError,
                match="incomplete rename",
            ):
                changed_python_files(tmp_path)

    def test_invalid_base_revision_raises_git_error(self, tmp_path):
        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                subprocess.CalledProcessError(
                    128,
                    "git",
                ),
            ]

            with pytest.raises(GitError) as exc:
                changed_python_files(
                    tmp_path,
                    "does-not-exist",
                )

        assert "relative to" in str(exc.value)

    def test_raises_when_git_returns_invalid_utf8(
        self,
        tmp_path,
    ):
        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0\xff.py\0"),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            with pytest.raises(GitError, match="invalid path encoding"):
                changed_python_files(tmp_path)

    def test_uses_requested_base_revision(self, tmp_path):
        py_file = tmp_path / "changed.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0changed.py\0"),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(
                tmp_path,
                "origin/main",
            )

        assert result == [py_file.resolve()]

        first_call = mock_run.call_args_list[0]
        assert first_call.args[0] == [
            "git",
            "diff",
            "--no-ext-diff",
            "--name-status",
            "-z",
            "--diff-filter=ACMRTUXB",
            "origin/main",
            "--",
        ]

    def test_disables_external_git_diff(self, tmp_path):
        py_file = tmp_path / "changed.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0changed.py\0"),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(tmp_path)

        assert result == [py_file.resolve()]

        first_call = mock_run.call_args_list[0]

        assert first_call.args[0] == [
            "git",
            "diff",
            "--no-ext-diff",
            "--name-status",
            "-z",
            "--diff-filter=ACMRTUXB",
            "HEAD",
            "--",
        ]

    def test_returns_empty_when_no_python_files_changed(self, tmp_path):
        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0README.md\0"),
                MagicMock(stdout=b"M\0pyproject.toml\0"),
                MagicMock(stdout=b"notes.txt\0"),
            ]

            result = changed_python_files(tmp_path)

        assert result == []

    def test_ignores_python_file_outside_requested_subdirectory(
        self,
        tmp_path,
    ):
        subdirectory = tmp_path / "src"
        subdirectory.mkdir()

        outside = tmp_path / "outside.py"
        outside.write_text("x = 1\n", encoding="utf-8")

        with (
            patch(
                "pyrift.git.repository_root",
                return_value=tmp_path,
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(stdout=b"M\0outside.py\0"),
                MagicMock(stdout=b""),
                MagicMock(stdout=b""),
            ]

            result = changed_python_files(subdirectory)

        assert result == []