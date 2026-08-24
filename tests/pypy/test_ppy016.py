import ast, textwrap
from pyrift.rules.pypy.ppy016_instance_dict_order import InstanceDictOrderRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY016:
    rule = InstanceDictOrderRule()

    def test_detects_instance_dict_access(self):
        findings = run(self.rule, "x = obj.__dict__")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY016"

    def test_detects_dict_iteration(self):
        findings = run(self.rule, "for k in obj.__dict__: pass")
        assert len(findings) == 1

    def test_suggestion_mentions_slots(self):
        findings = run(self.rule, "obj.__dict__")
        assert "__slots__" in findings[0].suggestion