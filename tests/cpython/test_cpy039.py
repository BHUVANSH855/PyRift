import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy039_zoneinfo import ZoneInfoRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY039:
    rule = ZoneInfoRule()

    def test_detects_import_zoneinfo(self):
        findings = run(self.rule, "import zoneinfo")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY039"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run(self.rule, "from zoneinfo import ZoneInfo")
        assert len(findings) == 1

    def test_clean_other_import(self):
        findings = run(self.rule, "import pytz")
        assert len(findings) == 0

    def test_suggestion_mentions_backport(self):
        findings = run(self.rule, "import zoneinfo")
        assert "backport" in findings[0].suggestion.lower()