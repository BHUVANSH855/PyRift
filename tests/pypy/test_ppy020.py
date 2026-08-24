import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.pypy.ppy020_kwargs_string_keys import KwargsStringKeysRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY020:
    rule = KwargsStringKeysRule()

    def test_detects_non_string_key_in_kwargs(self):
        findings = run(self.rule, "dict(**{1: 'value'})")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY020"
        assert findings[0].severity == Severity.ERROR

    def test_clean_string_keys(self):
        findings = run(self.rule, "dict(**{'key': 'value'})")
        assert len(findings) == 0

    def test_clean_regular_dict(self):
        findings = run(self.rule, "d = {1: 'value'}")
        assert len(findings) == 0

    def test_suggestion_mentions_string(self):
        findings = run(self.rule, "dict(**{1: 'x'})")
        assert "string" in findings[0].suggestion.lower()