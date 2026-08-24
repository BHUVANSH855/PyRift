import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy044_exception_chaining import ExceptionChainingRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY044:
    rule = ExceptionChainingRule()

    def test_detects_except_as(self):
        src = """
try:
    risky()
except ValueError as e:
    handle(e)
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY044"
        assert findings[0].severity == Severity.INFO

    def test_clean_except_no_name(self):
        src = """
try:
    risky()
except ValueError:
    pass
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_saved(self):
        src = "try:\n    x()\nexcept Exception as e:\n    pass"
        findings = run(self.rule, src)
        assert "saved" in findings[0].suggestion.lower() or \
               "assign" in findings[0].suggestion.lower()