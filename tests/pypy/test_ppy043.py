import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy043_slots_memory import SlotsMemorypyRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY043:
    rule = SlotsMemorypyRule()

    def test_detects_slots_definition(self):
        src = """
class Point:
    __slots__ = ['x', 'y']
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY043"
        assert findings[0].severity == Severity.INFO

    def test_clean_class_without_slots(self):
        src = """
class Point:
    def __init__(self):
        self.x = 0
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_measure(self):
        src = "class X:\n    __slots__ = ['a']"
        findings = run(self.rule, src)
        assert "measure" in findings[0].suggestion.lower() or \
               "memory" in findings[0].suggestion.lower()