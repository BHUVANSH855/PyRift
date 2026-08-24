import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy020_datetime_utc import DatetimeUTCRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY020:
    rule = DatetimeUTCRule()

    def test_detects_datetime_utc(self):
        findings = run(self.rule, "import datetime\ntz = datetime.UTC")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY020"
        assert findings[0].severity == Severity.ERROR

    def test_clean_timezone_utc(self):
        findings = run(self.rule, "import datetime\ntz = datetime.timezone.utc")
        assert len(findings) == 0

    def test_suggestion_mentions_timezone_utc(self):
        findings = run(self.rule, "datetime.UTC")
        assert "timezone.utc" in findings[0].suggestion.lower()