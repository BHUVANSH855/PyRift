import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy036_datetime_utcnow import DatetimeUtcnowRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY036:
    rule = DatetimeUtcnowRule()

    def test_detects_utcnow(self):
        findings = run(self.rule,
            "import datetime\nnow = datetime.datetime.utcnow()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY036"
        assert findings[0].severity == Severity.WARNING

    def test_clean_now_with_utc(self):
        findings = run(self.rule,
            "datetime.datetime.now(datetime.timezone.utc)")
        assert len(findings) == 0

    def test_suggestion_mentions_now(self):
        findings = run(self.rule, "datetime.utcnow()")
        assert "now" in findings[0].suggestion.lower()