import ast, textwrap
from pyrift.rules.pypy.ppy026_builtins_module import BuiltinsModuleRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY026:
    rule = BuiltinsModuleRule()

    def test_detects_builtins_access(self):
        findings = run(self.rule, "x = __builtins__")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY026"

    def test_detects_builtins_isinstance(self):
        findings = run(self.rule,
            "if isinstance(__builtins__, dict): pass")
        assert len(findings) == 1

    def test_suggestion_mentions_builtins_module(self):
        findings = run(self.rule, "__builtins__")
        assert "builtins" in findings[0].suggestion.lower()