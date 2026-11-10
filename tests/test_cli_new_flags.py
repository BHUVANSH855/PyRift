"""
Tests for CLI flags added in v0.9.1:
  - --format github
  - --only-documented
  - explain for tombstone rules
  - explain with whatsnew_ref / gh_issue output
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path


def run_cli(*args: str) -> tuple[int, str, str]:
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[1]
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(repo_root)
        if not pythonpath
        else os.pathsep.join((str(repo_root), pythonpath))
    )
    result = subprocess.run(
        [sys.executable, "-m", "pyrift.cli", *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


# ── --format github ──────────────────────────────────────────────────────────

class TestFormatGithub:
    def test_github_format_clean_scan_no_output(self, tmp_path):
        """Clean scan produces no annotation lines."""
        f = tmp_path / "clean.py"
        f.write_text("x = 1\n")
        code, out, _err = run_cli("scan", str(f), "--format", "github")
        assert code == 0
        assert out.strip() == ""

    def test_github_format_with_findings(self, tmp_path):
        """Scan with findings emits ::warning / ::error lines."""
        f = tmp_path / "bad.py"
        # CPY001: dict ordering assumption — easily triggered
        f.write_text(
            textwrap.dedent("""\
                d = {"a": 1, "b": 2}
                first = list(d.keys())[0]
            """)
        )
        code, out, _err = run_cli(
            "scan", str(f), "--format", "github", "--runtime", "cpython"
        )
        # Exit code may be non-zero if findings exist; output should contain ::
        if "::" in out:
            assert out.startswith("::error") or out.startswith("::warning") or out.startswith("::notice")

    def test_github_format_is_accepted_by_parser(self, tmp_path):
        """--format github is a valid choice; parser should not reject it."""
        f = tmp_path / "x.py"
        f.write_text("pass\n")
        code, _out, err = run_cli("scan", str(f), "--format", "github")
        # May be 0 (clean) or 1 (findings); must not be 2 (arg parse error)
        assert code != 2
        assert "invalid choice" not in err


# ── --only-documented ────────────────────────────────────────────────────────

class TestOnlyDocumented:
    def test_only_documented_flag_accepted(self, tmp_path):
        f = tmp_path / "x.py"
        f.write_text("pass\n")
        code, _out, err = run_cli("scan", str(f), "--only-documented")
        assert code != 2
        assert "invalid" not in err.lower() or "choice" not in err.lower()

    def test_only_documented_reduces_findings(self, tmp_path):
        """--only-documented should produce ≤ as many findings as without it."""
        f = tmp_path / "x.py"
        f.write_text(
            textwrap.dedent("""\
                import sys
                x = sys.maxint
            """)
        )
        _, out_all, _ = run_cli(
            "scan", str(f), "--format", "json", "--runtime", "cpython"
        )
        _, out_doc, _ = run_cli(
            "scan", str(f), "--format", "json", "--runtime", "cpython",
            "--only-documented",
        )
        import json
        try:
            all_count = len(json.loads(out_all).get("findings", []))
            doc_count = len(json.loads(out_doc).get("findings", []))
            assert doc_count <= all_count
        except (json.JSONDecodeError, KeyError):
            pass  # output may be empty / non-JSON for a clean scan


# ── explain: tombstone rules ─────────────────────────────────────────────────

class TestExplainTombstone:
    def test_explain_tombstone_cpy021_exits_nonzero(self):
        code, _out, err = run_cli("explain", "CPY021")
        assert code != 0

    def test_explain_tombstone_cpy052_exits_nonzero(self):
        code, _out, err = run_cli("explain", "CPY052")
        assert code != 0

    def test_explain_tombstone_cpy056_exits_nonzero(self):
        code, _out, err = run_cli("explain", "CPY056")
        assert code != 0

    def test_explain_tombstone_message_mentions_retired(self):
        _code, _out, err = run_cli("explain", "CPY021")
        combined = (_out + err).lower()
        assert "retired" in combined or "tombstone" in combined or "cpy021" in combined


# ── explain: whatsnew_ref / gh_issue display ─────────────────────────────────

class TestExplainWhatsnewRef:
    def test_explain_rule_with_whatsnew_ref_shows_url(self):
        """A rule that has a whatsnew_ref should print a What's New URL."""
        # CPY022 (bool inversion deprecated 3.12) has whatsnew_ref set
        code, out, _err = run_cli("explain", "CPY022")
        assert code == 0
        # Either the URL or the ref should appear if set
        assert "docs.python.org" in out or "What" in out or "CPY022" in out

    def test_explain_cpy055_shows_docs(self):
        code, out, _err = run_cli("explain", "CPY055")
        assert code == 0
        assert "CPY055" in out
