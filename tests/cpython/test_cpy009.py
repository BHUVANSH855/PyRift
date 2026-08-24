import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy009_exception_group import ExceptionGroupRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY009:
    rule = ExceptionGroupRule()

    def test_detects_exception_group(self):
        findings = run(self.rule, "eg = ExceptionGroup('errors', [e1, e2])")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY009"
        assert findings[0].severity == Severity.ERROR

    def test_detects_base_exception_group(self):
        findings = run(self.rule, "eg = BaseExceptionGroup('errors', [e])")
        assert len(findings) == 1

    def test_clean_regular_exception(self):
        findings = run(self.rule, "raise ValueError('oops')")
        assert len(findings) == 0

    def test_suggestion_mentions_backport(self):
        findings = run(self.rule, "ExceptionGroup('x', [])")
        assert "exceptiongroup" in findings[0].suggestion.lower()