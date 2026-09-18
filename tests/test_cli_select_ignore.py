"""
Tests for the --select/--ignore rule selection flags (2026-09 audit
item #78).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import pytest

from pyrift.cli import _resolve_selected_rules
from pyrift.scanner import ALL_RULES


def run_cli(*args: str) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pyrift.cli", *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class _Args(argparse.Namespace):
    """Minimal stand-in for argparse.Namespace for unit-level tests."""

    def __init__(self, select=None, ignore=None):
        super().__init__()
        self.select = select
        self.ignore = ignore


class TestResolveSelectedRulesUnit:
    def test_no_flags_returns_none(self):
        assert _resolve_selected_rules(_Args()) is None

    def test_select_returns_only_named_rules(self):
        rules = _resolve_selected_rules(_Args(select="CPY038,CPY067"))
        assert rules is not None
        ids = {r.rule_id for r in rules}
        assert ids == {"CPY038", "CPY067"}

    def test_select_is_case_insensitive(self):
        rules = _resolve_selected_rules(_Args(select="cpy038"))
        assert rules is not None
        assert {r.rule_id for r in rules} == {"CPY038"}

    def test_select_strips_whitespace(self):
        rules = _resolve_selected_rules(_Args(select=" CPY038 , CPY067 "))
        assert rules is not None
        assert {r.rule_id for r in rules} == {"CPY038", "CPY067"}

    def test_ignore_returns_all_but_named_rules(self):
        rules = _resolve_selected_rules(_Args(ignore="CPY038"))
        assert rules is not None
        ids = {r.rule_id for r in rules}
        assert "CPY038" not in ids
        assert len(rules) == len(ALL_RULES) - 1

    def test_unknown_rule_in_select_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            _resolve_selected_rules(_Args(select="CPY9999"))
        assert exc_info.value.code == 2

    def test_unknown_rule_in_ignore_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            _resolve_selected_rules(_Args(ignore="NOTAREALRULE"))
        assert exc_info.value.code == 2

    def test_select_and_ignore_together_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            _resolve_selected_rules(_Args(select="CPY038", ignore="CPY067"))
        assert exc_info.value.code == 2


class TestSelectIgnoreEndToEnd:
    """Full CLI subprocess tests against real source triggering two
    different rules, so filtering is observable in real output."""

    SRC = (
        "import sys\n"
        "sys.path.append(b'/foo')\n"
        "\n"
        "import functools\n"
        "functools.reduce(function=f, sequence=y)\n"
    )

    def test_select_narrows_to_named_rule(self, tmp_path):
        target = tmp_path / "mod.py"
        target.write_text(self.SRC)

        code, out, _err = run_cli(
            "scan", str(target), "--select", "CPY078",
            "--exit-zero", "--format", "json",
        )
        assert code == 0
        data = json.loads(out)
        rule_ids = {f["rule_id"] for f in data["findings"]}
        assert rule_ids == {"CPY078"}

    def test_ignore_excludes_named_rule(self, tmp_path):
        target = tmp_path / "mod.py"
        target.write_text(self.SRC)

        code, out, _err = run_cli(
            "scan", str(target), "--ignore", "CPY078",
            "--exit-zero", "--format", "json",
        )
        assert code == 0
        data = json.loads(out)
        rule_ids = {f["rule_id"] for f in data["findings"]}
        assert "CPY078" not in rule_ids
        assert "CPY030" in rule_ids

    def test_no_filter_shows_both(self, tmp_path):
        target = tmp_path / "mod.py"
        target.write_text(self.SRC)

        code, out, _err = run_cli(
            "scan", str(target), "--exit-zero", "--format", "json",
        )
        assert code == 0
        data = json.loads(out)
        rule_ids = {f["rule_id"] for f in data["findings"]}
        assert {"CPY030", "CPY078"} <= rule_ids

    def test_unknown_rule_id_is_a_hard_error(self, tmp_path):
        target = tmp_path / "mod.py"
        target.write_text(self.SRC)

        code, _out, err = run_cli(
            "scan", str(target), "--select", "CPY9999", "--exit-zero",
        )
        assert code == 2
        assert "CPY9999" in err

    def test_select_and_ignore_together_is_a_hard_error(self, tmp_path):
        target = tmp_path / "mod.py"
        target.write_text(self.SRC)

        code, _out, err = run_cli(
            "scan", str(target),
            "--select", "CPY078", "--ignore", "CPY030",
            "--exit-zero",
        )
        assert code == 2
        assert "cannot be combined" in err


class TestPyriftConfigFileIntegration:
    """2026-09 audit item #34: [tool.pyrift] applies as a default, CLI
    flags override it, and --no-project-config disables it -- all
    verified end-to-end through the real CLI, not just unit calls."""

    SRC = (
        "import sys\n"
        "sys.path.append(b'/foo')\n"
        "\n"
        "import functools\n"
        "functools.reduce(function=f, sequence=y)\n"
    )

    def _write_project(self, tmp_path, tool_pyrift_body: str):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\n\n'
            "[tool.pyrift]\n" + tool_pyrift_body
        )
        target = tmp_path / "mod.py"
        target.write_text(self.SRC)
        return target

    def test_config_select_applies_with_no_cli_flags(self, tmp_path):
        target = self._write_project(tmp_path, 'select = ["CPY078"]\n')
        code, out, _err = run_cli(
            "scan", str(target), "--exit-zero", "--format", "json",
        )
        assert code == 0
        rule_ids = {f["rule_id"] for f in json.loads(out)["findings"]}
        assert rule_ids == {"CPY078"}

    def test_config_ignore_applies_with_no_cli_flags(self, tmp_path):
        target = self._write_project(tmp_path, 'ignore = ["CPY078"]\n')
        code, out, _err = run_cli(
            "scan", str(target), "--exit-zero", "--format", "json",
        )
        assert code == 0
        rule_ids = {f["rule_id"] for f in json.loads(out)["findings"]}
        assert "CPY078" not in rule_ids
        assert "CPY030" in rule_ids

    def test_cli_select_flag_overrides_config_file(self, tmp_path):
        target = self._write_project(tmp_path, 'select = ["CPY078"]\n')
        code, out, _err = run_cli(
            "scan", str(target), "--select", "CPY030",
            "--exit-zero", "--format", "json",
        )
        assert code == 0
        rule_ids = {f["rule_id"] for f in json.loads(out)["findings"]}
        assert rule_ids == {"CPY030"}

    def test_no_project_config_disables_config_file_selection(self, tmp_path):
        target = self._write_project(tmp_path, 'select = ["CPY078"]\n')
        code, out, _err = run_cli(
            "scan", str(target), "--no-project-config",
            "--exit-zero", "--format", "json",
        )
        assert code == 0
        rule_ids = {f["rule_id"] for f in json.loads(out)["findings"]}
        assert {"CPY030", "CPY078"} <= rule_ids

    def test_invalid_config_both_select_and_ignore_is_hard_error(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\n\n'
            "[tool.pyrift]\n"
            'select = ["CPY078"]\n'
            'ignore = ["CPY030"]\n'
        )
        target = tmp_path / "mod.py"
        target.write_text(self.SRC)

        code, _out, err = run_cli(
            "scan", str(target), "--exit-zero",
        )
        assert code == 2
        assert "tool.pyrift" in err
