import ast
import textwrap

from pyrift.rules.pypy.ppy019_nan_identity import NanIdentityRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY019:
    rule = NanIdentityRule()

    def test_detects_float_nan(self):
        findings = run(self.rule, "x = float('nan')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY019"

    def test_detects_uppercase_nan(self):
        findings = run(self.rule, "x = float('NaN')")
        assert len(findings) == 1

    def test_clean_regular_float(self):
        findings = run(self.rule, "x = float('1.5')")
        assert len(findings) == 0

    def test_suggestion_mentions_isnan(self):
        findings = run(self.rule, "float('nan')")
        assert "isnan" in findings[0].suggestion.lower()