import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy073_sqlite3_version import Sqlite3VersionRemovedRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY073:
    rule = Sqlite3VersionRemovedRule()

    def test_detects_version(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY073"
        assert findings[0].severity == Severity.ERROR

    def test_detects_version_info(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version_info")
        assert len(findings) == 1

    def test_clean_sqlite_version(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.sqlite_version")
        assert len(findings) == 0

    def test_suggestion_mentions_sqlite_version(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert "sqlite_version" in findings[0].suggestion
