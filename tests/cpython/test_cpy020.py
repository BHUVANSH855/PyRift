import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy020_datetime_utc import DatetimeUTCRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY020:
    rule = DatetimeUTCRule()

    def test_detects_datetime_utc(self):
        findings = run(
            self.rule,
            "import datetime\ntz = datetime.UTC",
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY020"
        assert findings[0].severity == Severity.ERROR

    def test_detects_datetime_utc_with_module_alias(self):
        findings = run(
            self.rule,
            "import datetime as dt\ntz = dt.UTC",
        )
        assert len(findings) == 1

    def test_detects_from_datetime_import_utc(self):
        findings = run(
            self.rule,
            "from datetime import UTC\ntz = UTC",
        )
        assert len(findings) == 1

    def test_detects_from_datetime_import_utc_with_alias(self):
        findings = run(
            self.rule,
            "from datetime import UTC as utc\ntz = utc",
        )
        assert len(findings) == 1

    def test_clean_timezone_utc(self):
        findings = run(
            self.rule,
            "import datetime\ntz = datetime.timezone.utc",
        )
        assert findings == []

    def test_clean_unrelated_utc_attribute(self):
        findings = run(
            self.rule,
            "obj = object()\ntz = obj.UTC",
        )
        assert findings == []

    def test_clean_unimported_datetime_name(self):
        findings = run(
            self.rule,
            "tz = datetime.UTC",
        )
        assert findings == []

    def test_clean_similarly_named_module(self):
        findings = run(
            self.rule,
            "import my_datetime\ntz = my_datetime.UTC",
        )
        assert findings == []

    def test_detects_function_local_datetime_import(self):
        findings = run(
            self.rule,
            "def f():\n    import datetime\n    return datetime.UTC\n",
        )
        assert len(findings) == 1

    def test_detects_multiple_datetime_utc_uses(self):
        findings = run(
            self.rule,
            "import datetime\na = datetime.UTC\nb = datetime.UTC\n",
        )
        assert len(findings) == 2

    def test_suggestion_mentions_timezone_utc(self):
        findings = run(
            self.rule,
            "import datetime\ntz = datetime.UTC",
        )
        assert "timezone.utc" in findings[0].suggestion.lower()

    def test_description_identifies_python_311_introduction(self):
        findings = run(
            self.rule,
            "import datetime\ntz = datetime.UTC",
        )
        assert "Python 3.11" in findings[0].description

    def test_affected_versions_end_at_python_310(self):
        findings = run(
            self.rule,
            "import datetime\ntz = datetime.UTC",
        )
        assert findings[0].affected_from == "3.0"
        assert findings[0].affected_until == "3.10"

    def test_docs_url_points_to_datetime_utc(self):
        findings = run(
            self.rule,
            "import datetime\ntz = datetime.UTC",
        )
        assert (
            findings[0].docs_url == "https://docs.python.org/3/library/datetime.html"
            "#datetime.UTC"
        )
