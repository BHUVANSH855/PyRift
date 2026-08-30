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

    def test_detects_datetime_module_alias(self):
        findings = run(
            self.rule,
            "import datetime as dt\n"
            "now = dt.datetime.utcnow()",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY036"

    def test_does_not_detect_unrelated_utcnow_method(self):
        findings = run(
            self.rule,
            "class Fake:\n"
            "    def utcnow(self):\n"
            "        return None\n"
            "\n"
            "fake = Fake()\n"
            "fake.utcnow()",
        )

        assert len(findings) == 0

    def test_does_not_detect_unrelated_class_utcnow(self):
        findings = run(
            self.rule,
            "class Fake:\n"
            "    @staticmethod\n"
            "    def utcnow():\n"
            "        return None\n"
            "\n"
            "Fake.utcnow()",
        )

        assert len(findings) == 0

    def test_suggestion_mentions_now(self):
        findings = run(
            self.rule,
            "import datetime\n"
            "datetime.datetime.utcnow()",
        )

        assert len(findings) == 1
        assert "now" in findings[0].suggestion.lower()