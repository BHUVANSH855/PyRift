import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy071_pty_master_slave_open import PtyMasterSlaveOpenRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY071:
    rule = PtyMasterSlaveOpenRule()

    def test_detects_master_open_import(self):
        findings = run(self.rule, "from pty import master_open")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY071"
        assert findings[0].severity == Severity.ERROR

    def test_detects_slave_open_import(self):
        findings = run(self.rule, "from pty import slave_open")
        assert len(findings) == 1

    def test_detects_master_open_call(self):
        findings = run(self.rule, "import pty\npty.master_open()")
        assert len(findings) == 1

    def test_clean_openpty(self):
        findings = run(self.rule, "import pty\npty.openpty()")
        assert len(findings) == 0

    def test_suggestion_mentions_openpty(self):
        findings = run(self.rule, "from pty import master_open")
        assert "openpty" in findings[0].suggestion
