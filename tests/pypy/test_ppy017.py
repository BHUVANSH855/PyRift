import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy017_del_existing_class import DelExistingClassRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY017:
    rule = DelExistingClassRule()

    def test_detects_del_assignment(self):
        findings = run(self.rule, "MyClass.__del__ = lambda self: None")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY017"
        assert findings[0].severity == Severity.ERROR

    def test_clean_del_in_class_body(self):
        src = """
class MyClass:
    def __del__(self):
        pass
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_class_body(self):
        findings = run(self.rule, "A.__del__ = lambda self: None")
        assert "class" in findings[0].suggestion.lower()