import ast, textwrap
from pyrift.rules.pypy.ppy009_id_stability import IdStabilityRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY009:
    rule = IdStabilityRule()

    def test_detects_id_call(self):
        findings = run(self.rule, "x = id(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY009"

    def test_suggestion_mentions_is(self):
        findings = run(self.rule, "id(obj)")
        assert "is" in findings[0].suggestion.lower()