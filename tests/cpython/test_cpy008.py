import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy008_slots_dict import SlotsDictRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY008:
    rule = SlotsDictRule()

    def test_detects_slots_with_base(self):
        src = """
class Base:
    pass
class Child(Base):
    __slots__ = ['x', 'y']
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY008"
        assert findings[0].severity == Severity.INFO

    def test_clean_slots_no_base(self):
        findings = run(self.rule, "class MyClass:\n    __slots__ = ['x']")
        assert len(findings) == 0

    def test_clean_object_base(self):
        findings = run(self.rule, "class MyClass(object):\n    __slots__ = ['x']")
        assert len(findings) == 0