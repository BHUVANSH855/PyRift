import ast
import textwrap

from pyrift.rules.pypy.ppy029_builtins_assign import BuiltinsAssignRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY029:
    rule = BuiltinsAssignRule()

    def test_detects_builtins_assignment(self):
        findings = run(self.rule, "__builtins__ = my_builtins")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY029"

    def test_clean_other_assignment(self):
        findings = run(self.rule, "x = 42")
        assert len(findings) == 0

    def test_suggestion_mentions_builtins_module(self):
        findings = run(self.rule, "__builtins__ = {}")
        assert "builtins" in findings[0].suggestion.lower()