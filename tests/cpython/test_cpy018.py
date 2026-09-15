import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy018_required import RequiredRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY018:
    rule = RequiredRule()

    def test_detects_required_import(self):
        findings = run(self.rule, "from typing import Required")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY018"
        assert findings[0].severity == Severity.ERROR

    def test_detects_not_required_import(self):
        findings = run(self.rule, "from typing import NotRequired")
        assert len(findings) == 1

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Optional")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import Required")
        assert "typing_extensions" in findings[0].suggestion.lower()

    def test_suggestion_is_valid_try_except_shape(self):
        findings = run(self.rule, "from typing import Required")
        suggestion = findings[0].suggestion

        assert "try:" in suggestion
        assert "from typing import Required" in suggestion
        assert "except ImportError:" in suggestion
        assert "from typing_extensions import Required" in suggestion

    def test_detects_required_alias(self):
        findings = run(
            self.rule,
            "from typing import Required as Req",
        )
        assert len(findings) == 1

    def test_detects_not_required_alias(self):
        findings = run(
            self.rule,
            "from typing import NotRequired as NotReq",
        )
        assert len(findings) == 1

    def test_detects_both_imports(self):
        findings = run(
            self.rule,
            "from typing import Required, NotRequired",
        )
        assert len(findings) == 2

    def test_detects_function_local_import(self):
        findings = run(
            self.rule,
            "def f():\n    from typing import Required\n",
        )
        assert len(findings) == 1

    def test_ignores_other_typing_names(self):
        findings = run(
            self.rule,
            "from typing import Any, Optional, TypedDict",
        )
        assert findings == []

    def test_ignores_same_names_from_other_module(self):
        findings = run(
            self.rule,
            "from other_module import Required, NotRequired",
        )
        assert findings == []

    def test_detects_insufficient_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 10):\n"
            "    from typing import Required\n",
        )
        assert len(findings) == 1

    def test_accepts_exact_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 11):\n"
            "    from typing import Required\n",
        )
        assert findings == []

    def test_accepts_newer_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 12):\n"
            "    from typing import NotRequired\n",
        )
        assert findings == []
