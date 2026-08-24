import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy016_typevartuple import TypeVarTupleRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

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