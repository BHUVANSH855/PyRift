import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy017_unpack import UnpackRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY017:
    rule = UnpackRule()

    def test_detects_unpack_import(self):
        findings = run(self.rule, "from typing import Unpack")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY017"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Union")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import Unpack")
        assert "typing_extensions" in findings[0].suggestion.lower()

    def test_detects_unpack_alias(self):
        findings = run(
            self.rule,
            "from typing import Unpack as U",
        )
        assert len(findings) == 1

    def test_detects_multiple_typing_imports(self):
        findings = run(
            self.rule,
            "from typing import Unpack, Union",
        )
        assert len(findings) == 1

    def test_ignores_other_typing_names(self):
        findings = run(
            self.rule,
            "from typing import Any, TypeVar, Union",
        )
        assert findings == []

    def test_detects_function_local_import(self):
        findings = run(
            self.rule,
            "def f():\n    from typing import Unpack\n",
        )
        assert len(findings) == 1

    def test_detects_insufficient_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 10):\n"
            "    from typing import Unpack\n",
        )
        assert len(findings) == 1

    def test_accepts_exact_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 11):\n"
            "    from typing import Unpack\n",
        )
        assert findings == []

    def test_accepts_newer_version_guard(self):
        findings = run(
            self.rule,
            "import sys\n"
            "if sys.version_info >= (3, 12):\n"
            "    from typing import Unpack\n",
        )
        assert findings == []

    def test_ignores_similarly_named_symbol(self):
        findings = run(
            self.rule,
            "from other_module import Unpack",
        )
        assert findings == []
