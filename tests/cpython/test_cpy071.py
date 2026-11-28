"""Tests for CPY071 — pty.master_open()/slave_open() deprecated 3.12, removed 3.14."""
import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy071_pty_master_slave_open import PtyMasterSlaveOpenRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")


class TestCPY071:
    rule = PtyMasterSlaveOpenRule()

    # ------------------------------------------------------------------ imports
    def test_detects_master_open_import(self):
        findings = run(self.rule, "from pty import master_open")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY071"
        assert findings[0].severity == Severity.ERROR

    def test_detects_slave_open_import(self):
        findings = run(self.rule, "from pty import slave_open")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY071"

    # ------------------------------------------------------------------ calls
    def test_detects_master_open_call(self):
        findings = run(self.rule, "import pty\npty.master_open()")
        assert len(findings) == 1

    def test_detects_slave_open_call(self):
        findings = run(self.rule, "import pty\npty.slave_open()")
        assert len(findings) == 1

    # ------------------------------------------------------------------ clean cases
    def test_clean_openpty(self):
        findings = run(self.rule, "import pty\npty.openpty()")
        assert len(findings) == 0

    def test_clean_unrelated_attribute(self):
        findings = run(self.rule, "other.master_open()")
        assert len(findings) == 0

    def test_clean_unrelated_import(self):
        findings = run(self.rule, "from pty import openpty")
        assert len(findings) == 0

    # ------------------------------------------------------------------ suggestion / description
    def test_suggestion_mentions_openpty(self):
        findings = run(self.rule, "from pty import master_open")
        assert "openpty" in findings[0].suggestion

    def test_description_mentions_deprecated(self):
        findings = run(self.rule, "from pty import master_open")
        assert "deprecated" in findings[0].description.lower()

    # ------------------------------------------------------------------ metadata
    def test_affected_from_is_3_12(self):
        """DeprecationWarning added in 3.12 (gh-85984) — rule should fire from 3.12."""
        findings = run(self.rule, "from pty import master_open")
        assert findings[0].affected_from == "3.12"

    def test_affected_until_is_empty(self):
        """Removed in 3.14 — no upper bound (fires forever from 3.12 onward)."""
        findings = run(self.rule, "from pty import master_open")
        assert findings[0].affected_until == ""
