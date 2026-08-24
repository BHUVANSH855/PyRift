import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy037_os_urandom import OsUrandomRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY037:
    rule = OsUrandomRule()

    def test_detects_os_urandom(self):
        findings = run(self.rule, "import os\nbytes = os.urandom(16)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY037"
        assert findings[0].severity == Severity.INFO

    def test_clean_secrets(self):
        findings = run(self.rule, "import secrets\nb = secrets.token_bytes(16)")
        assert len(findings) == 0

    def test_suggestion_mentions_secrets(self):
        findings = run(self.rule, "os.urandom(32)")
        assert "secrets" in findings[0].suggestion.lower()