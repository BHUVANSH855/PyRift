import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy010_dataclass_slots import DataclassSlotsRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY010:
    rule = DataclassSlotsRule()

    def test_detects_dataclass_slots(self):
        src = """
from dataclasses import dataclass
@dataclass(slots=True)
class Point:
    x: float
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY010"
        assert findings[0].severity == Severity.ERROR

    def test_clean_dataclass_no_slots(self):
        findings = run(self.rule, "@dataclass\nclass Point:\n    x: float")
        assert len(findings) == 0

    def test_clean_dataclass_slots_false(self):
        findings = run(self.rule, "@dataclass(slots=False)\nclass Point:\n    x: float")
        assert len(findings) == 0

    def test_suggestion_mentions_requires_python(self):
        src = "@dataclass(slots=True)\nclass X:\n    a: int"
        findings = run(self.rule, src)
        assert "pyproject" in findings[0].suggestion.lower()