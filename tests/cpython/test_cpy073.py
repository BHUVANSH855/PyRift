import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy073_sqlite3_version import Sqlite3VersionRemovedRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY073:
    rule = Sqlite3VersionRemovedRule()

    # --- detection: attribute-access form ---

    def test_detects_version(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY073"
        assert findings[0].severity == Severity.ERROR

    def test_detects_version_info(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version_info")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY073"

    def test_detects_both_attrs_in_one_file(self):
        src = "import sqlite3\nx = sqlite3.version\ny = sqlite3.version_info"
        findings = run(self.rule, src)
        assert len(findings) == 2
        rule_ids = {f.rule_id for f in findings}
        assert rule_ids == {"CPY073"}

    # --- detection: from-import form ---

    def test_detects_from_import_version(self):
        findings = run(self.rule, "from sqlite3 import version")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY073"

    def test_detects_from_import_version_info(self):
        findings = run(self.rule, "from sqlite3 import version_info")
        assert len(findings) == 1

    def test_detects_both_from_imports(self):
        """Alias-level positions: each alias gets its own finding."""
        findings = run(self.rule, "from sqlite3 import version, version_info")
        assert len(findings) == 2

    def test_detects_both_from_imports_separate_lines(self):
        src = "from sqlite3 import version\nfrom sqlite3 import version_info"
        findings = run(self.rule, src)
        assert len(findings) == 2

    # --- alias form (import sqlite3 as ...) should still fire ---

    def test_detects_attr_in_expression(self):
        src = "import sqlite3\nprint(sqlite3.version)"
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_detects_attr_assigned(self):
        src = "import sqlite3\nv = sqlite3.version_info[0]"
        findings = run(self.rule, src)
        assert len(findings) == 1

    # --- negative cases ---

    def test_clean_sqlite_version(self):
        """sqlite3.sqlite_version is the correct replacement — must NOT fire."""
        findings = run(self.rule, "import sqlite3\nsqlite3.sqlite_version")
        assert len(findings) == 0

    def test_clean_sqlite_version_info(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.sqlite_version_info")
        assert len(findings) == 0

    def test_clean_unrelated_attribute(self):
        findings = run(self.rule, "other.version")
        assert len(findings) == 0

    def test_clean_unrelated_module_import(self):
        findings = run(self.rule, "from os import version")
        assert len(findings) == 0

    def test_clean_no_sqlite3_at_all(self):
        findings = run(self.rule, "x = 1 + 2")
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    def test_clean_version_on_other_obj(self):
        """obj.version where obj is not sqlite3 must not fire."""
        findings = run(self.rule, "import pkg\npkg.version")
        assert len(findings) == 0

    # --- finding content ---

    def test_suggestion_mentions_sqlite_version(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert "sqlite_version" in findings[0].suggestion

    def test_suggestion_mentions_sqlite_version_info(self):
        findings = run(self.rule, "from sqlite3 import version_info")
        assert "sqlite_version_info" in findings[0].suggestion

    def test_description_mentions_deprecated(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert "deprecated" in findings[0].description.lower()

    def test_description_mentions_removed(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version_info")
        assert "removed" in findings[0].description.lower()

    def test_description_mentions_deprecated_version(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert "3.12" in findings[0].description

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert "3.14" in findings[0].description

    def test_docs_url_points_to_whatsnew_3_14(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert "3.14" in findings[0].docs_url

    def test_severity_is_error(self):
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert findings[0].severity == Severity.ERROR

    # --- metadata ---

    def test_affected_from_is_3_12(self):
        """DeprecationWarning added in 3.12 — rule should fire from 3.12."""
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert findings[0].affected_from == "3.12"

    def test_affected_until_is_empty(self):
        """Removed in 3.14 — no upper bound (fires forever from 3.12 onward)."""
        findings = run(self.rule, "import sqlite3\nsqlite3.version")
        assert findings[0].affected_until == ""