import ast
import textwrap

from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY027:
    rule = ModuleAttrDeleteRule()

    def test_detects_del_attribute(self):
        findings = run(self.rule, "del module.attr")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY027"

    def test_detects_del_class_attr(self):
        findings = run(self.rule, "del MyClass.method")
        assert len(findings) == 1

    def test_clean_del_variable(self):
        findings = run(self.rule, "del x")
        assert len(findings) == 0

    def test_suggestion_mentions_none(self):
        findings = run(self.rule, "del obj.attr")
        assert "none" in findings[0].suggestion.lower()