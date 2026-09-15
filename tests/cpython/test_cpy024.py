import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy024_typeguard import TypeGuardRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY024:
    rule = TypeGuardRule()

    def test_detects_typeguard_import(self):
        findings = run(self.rule, "from typing import TypeGuard")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY024"
        assert findings[0].severity == Severity.ERROR

    def test_detects_aliased_typeguard_import(self):
        findings = run(self.rule, "from typing import TypeGuard as TG")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY024"

    def test_detects_local_typeguard_import(self):
        findings = run(
            self.rule,
            """
            def func():
                from typing import TypeGuard
                return TypeGuard
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY024"

    def test_detects_multiple_typeguard_imports(self):
        findings = run(
            self.rule,
            """
            from typing import TypeGuard
            from typing import TypeGuard as TG
            """,
        )
        assert len(findings) == 2

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Optional")
        assert findings == []

    def test_clean_typing_extensions_typeguard(self):
        findings = run(
            self.rule,
            "from typing_extensions import TypeGuard",
        )
        assert findings == []

    def test_clean_unrelated_module_typeguard(self):
        findings = run(
            self.rule,
            "from other_module import TypeGuard",
        )
        assert findings == []

    def test_clean_typing_module_import_without_typeguard(self):
        findings = run(
            self.rule,
            "import typing",
        )
        assert findings == []

    def test_clean_typeguard_name_without_import(self):
        findings = run(
            self.rule,
            """
            TypeGuard = something_else
            result = TypeGuard
            """,
        )
        assert findings == []

    def test_does_not_flag_python_310_guard(self):
        findings = run(
            self.rule,
            """
            import sys

            if sys.version_info >= (3, 10):
                from typing import TypeGuard
            """,
        )
        assert findings == []

    def test_does_not_flag_newer_python_guard(self):
        findings = run(
            self.rule,
            """
            import sys

            if sys.version_info >= (3, 11):
                from typing import TypeGuard
            """,
        )
        assert findings == []

    def test_insufficient_python_39_guard_still_reports(self):
        findings = run(
            self.rule,
            """
            import sys

            if sys.version_info >= (3, 9):
                from typing import TypeGuard
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY024"

    def test_detects_typeguard_in_function_scope_without_guard(self):
        findings = run(
            self.rule,
            """
            def func():
                from typing import TypeGuard
                return TypeGuard
            """,
        )
        assert len(findings) == 1

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import TypeGuard")
        assert "typing_extensions" in findings[0].suggestion.lower()

    def test_description_identifies_python_310(self):
        findings = run(self.rule, "from typing import TypeGuard")
        assert "Python 3.10" in findings[0].description

    def test_affected_versions(self):
        findings = run(self.rule, "from typing import TypeGuard")
        assert findings[0].affected_from == "3.0"
        assert findings[0].affected_until == "3.9"

    def test_docs_url_points_to_pep_647(self):
        findings = run(self.rule, "from typing import TypeGuard")
        assert findings[0].docs_url == "https://peps.python.org/pep-647/"
