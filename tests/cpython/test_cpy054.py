import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy054_int_trunc import IntTruncRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY054:
    rule = IntTruncRule()

    def test_detects_trunc_method(self):
        src = """
class MyNumber:
    def __trunc__(self):
        return int(self._value)
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY054"
        assert findings[0].severity == Severity.ERROR

    def test_clean_int_method(self):
        src = """
class MyNumber:
    def __int__(self):
        return int(self._value)
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_int(self):
        src = """
class X:
    def __trunc__(self): return 0
"""
        findings = run(self.rule, src)
        assert "__int__" in findings[0].suggestion