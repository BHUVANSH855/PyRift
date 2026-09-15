import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy015_never import NeverRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY015:
    rule = NeverRule()

    def test_detects_never_import(self):
        findings = run(self.rule, "from typing import Never")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY015"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import NoReturn")
        assert findings == []

    def test_clean_typing_extensions_never(self):
        findings = run(
            self.rule,
            "from typing_extensions import Never",
        )
        assert findings == []

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import Never")
        assert "typing_extensions" in findings[0].suggestion.lower()

    def test_detects_never_alias(self):
        findings = run(
            self.rule,
            "from typing import Never as Bottom",
        )
        assert len(findings) == 1

    def test_detects_multiple_typing_imports(self):
        findings = run(
            self.rule,
            "from typing import Never, NoReturn",
        )
        assert len(findings) == 1

    def test_ignores_other_typing_names(self):
        findings = run(
            self.rule,
            "from typing import Any, NoReturn, Optional",
        )
        assert findings == []

    def test_detects_function_local_import(self):
        findings = run(
            self.rule,
            "def f():\n    from typing import Never\n",
        )
        assert len(findings) == 1

    def test_detects_insufficient_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 10):\n"
            "    from typing import Never\n",
        )
        assert len(findings) == 1

    def test_accepts_exact_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 11):\n"
            "    from typing import Never\n",
        )
        assert findings == []

    def test_accepts_newer_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 12):\n"
            "    from typing import Never\n",
        )
        assert findings == []

    def test_finding_reports_python_310_as_last_affected_version(self):
        findings = run(
            self.rule,
            "from typing import Never",
        )
        assert findings[0].affected_from == "3.0"
        assert findings[0].affected_until == "3.10"

    def test_docs_url_points_to_typing_never(self):
        findings = run(
            self.rule,
            "from typing import Never",
        )
        assert (
            findings[0].docs_url == "https://docs.python.org/3.11/library/typing.html"
            "#typing.Never"
        )

    def test_description_identifies_python_311_introduction(self):
        findings = run(
            self.rule,
            "from typing import Never",
        )
        assert "added in Python 3.11" in findings[0].description
