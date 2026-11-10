import ast
import textwrap

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

    def test_detects_union_in_issubclass(self):
        """issubclass() with X | Y union also requires Python 3.10+."""
        findings = run(self.rule, "issubclass(cls, int | str)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY003"

    def test_detects_three_way_union(self):
        """Nested union: int | str | bytes triggers once per BinOp containing |."""
        findings = run(self.rule, "isinstance(x, int | str | bytes)")
        # At least one finding; outer BinOp wraps the whole expression
        assert len(findings) >= 1
        assert all(f.rule_id == "CPY003" for f in findings)

    def test_clean_isinstance_with_tuple(self):
        findings = run(self.rule, "isinstance(x, (int, str))")
        assert len(findings) == 0

    def test_union_in_type_annotation_not_flagged(self):
        """X | Y in a type annotation is fine (PEP 563 / runtime not evaluated)."""
        src = "def f(x: int | str) -> None: pass"
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_bitwise_or_on_integers_not_flagged(self):
        """Bitwise OR on plain integers must not be flagged."""
        findings = run(self.rule, "result = 0b1010 | 0b0101")
        assert len(findings) == 0