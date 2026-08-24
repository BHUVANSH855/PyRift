import ast
import textwrap

from pyrift.rules.pypy.ppy025_set_ordering import SetOrderingRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY025:
    rule = SetOrderingRule()

    def test_detects_list_of_set_literal(self):
        findings = run(self.rule, "x = list({'a', 'b', 'c'})")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY025"

    def test_clean_list_of_list(self):
        findings = run(self.rule, "x = list(['a', 'b', 'c'])")
        assert len(findings) == 0

    def test_suggestion_mentions_sorted(self):
        findings = run(self.rule, "list({'a', 'b'})")
        assert "sorted" in findings[0].suggestion.lower()