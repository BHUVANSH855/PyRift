import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.pypy.ppy011_array import ArrayTypeCodeRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY011:
    rule = ArrayTypeCodeRule()

    def test_detects_array_u_typecode(self):
        findings = run(self.rule, "from array import array\narray('u', 'hello')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY011"
        assert findings[0].severity == Severity.ERROR

    def test_clean_array_other_typecode(self):
        findings = run(self.rule, "array('i', [1, 2, 3])")
        assert len(findings) == 0

    def test_suggestion_mentions_replacement(self):
        findings = run(self.rule, "array('u', 'x')")
        assert findings[0].suggestion != ""