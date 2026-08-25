import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy055_notimplemented_bool import NotImplementedBoolRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY055:
    rule = NotImplementedBoolRule()

    def test_detects_if_notimplemented(self):
        findings = run(self.rule, "if NotImplemented: pass")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY055"
        assert findings[0].severity == Severity.ERROR

    def test_detects_not_notimplemented(self):
        findings = run(self.rule, "if not NotImplemented: pass")
        assert len(findings) == 1

    def test_detects_bool_notimplemented(self):
        findings = run(self.rule, "x = bool(NotImplemented)")
        assert len(findings) == 1

    def test_clean_return_notimplemented(self):
        src = """
def __add__(self, other):
    return NotImplemented
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_notimplementederror(self):
        findings = run(self.rule, "if NotImplemented: pass")
        assert "NotImplementedError" in findings[0].suggestion