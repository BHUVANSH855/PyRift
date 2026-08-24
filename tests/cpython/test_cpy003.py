import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy003_union_type_syntax import UnionTypeSyntaxRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY003:
    rule = UnionTypeSyntaxRule()

    def test_detects_union_in_isinstance(self):
        findings = run(self.rule, "isinstance(x, int | str)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY003"
        assert findings[0].severity == Severity.ERROR

    def test_clean_isinstance_with_tuple(self):
        findings = run(self.rule, "isinstance(x, (int, str))")
        assert len(findings) == 0