import ast, textwrap
from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY006:
    rule = BuiltinMonkeyPatchRule()

    def test_detects_list_patch(self):
        findings = run(self.rule, "list.custom = lambda self: None")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY006"

    def test_detects_dict_patch(self):
        findings = run(self.rule, "dict.merge = lambda self, other: None")
        assert len(findings) == 1

    def test_clean_subclass(self):
        findings = run(self.rule, "class MyList(list):\n    def custom(self): pass")
        assert len(findings) == 0

    def test_suggestion_mentions_subclass(self):
        findings = run(self.rule, "str.shout = lambda self: self.upper()")
        assert "subclass" in findings[0].suggestion.lower()