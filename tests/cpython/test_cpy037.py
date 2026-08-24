import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy037_datetime_utcfromtimestamp import (
    DatetimeUtcfromtimestampRule,
)


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY037:
    rule = DatetimeUtcfromtimestampRule()

    def test_detects_utcfromtimestamp(self):
        findings = run(self.rule,
            "import datetime\ndt = datetime.datetime.utcfromtimestamp(ts)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY037"
        assert findings[0].severity == Severity.WARNING

    def test_clean_fromtimestamp_with_tz(self):
        findings = run(self.rule,
            "datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)")
        assert len(findings) == 0

    def test_suggestion_mentions_fromtimestamp(self):
        findings = run(self.rule, "datetime.utcfromtimestamp(ts)")
        assert "fromtimestamp" in findings[0].suggestion.lower()