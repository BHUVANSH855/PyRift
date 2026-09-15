import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy016_typevartuple import TypeVarTupleRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY016:
    rule = TypeVarTupleRule()

    def test_detects_typevartuple_import(self):
        findings = run(self.rule, "from typing import TypeVarTuple")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY016"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import TypeVar")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import TypeVarTuple")
        assert "typing_extensions" in findings[0].suggestion.lower()

    def test_detects_typevartuple_alias(self):
        findings = run(
            self.rule,
            "from typing import TypeVarTuple as Ts",
        )
        assert len(findings) == 1

    def test_detects_multiple_typing_imports(self):
        findings = run(
            self.rule,
            "from typing import TypeVarTuple, TypeVar",
        )
        assert len(findings) == 1

    def test_ignores_other_typing_names(self):
        findings = run(
            self.rule,
            "from typing import Any, TypeVar, Optional",
        )
        assert findings == []

    def test_detects_function_local_import(self):
        findings = run(
            self.rule,
            "def f():\n    from typing import TypeVarTuple\n",
        )
        assert len(findings) == 1

    def test_detects_insufficient_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 10):\n"
            "    from typing import TypeVarTuple\n",
        )
        assert len(findings) == 1

    def test_accepts_exact_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 11):\n"
            "    from typing import TypeVarTuple\n",
        )
        assert findings == []

    def test_accepts_newer_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 12):\n"
            "    from typing import TypeVarTuple\n",
        )
        assert findings == []

    def test_ignores_similarly_named_symbol(self):
        findings = run(
            self.rule,
            "from other_module import TypeVarTuple",
        )
        assert findings == []
