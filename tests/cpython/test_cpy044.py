import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy044_math_gcd_multi import MathGcdMultiRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY044:
    rule = MathGcdMultiRule()

    def test_detects_gcd_three_args(self):
        findings = run(self.rule, "import math\nmath.gcd(4, 6, 8)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY044"
        assert findings[0].severity == Severity.ERROR

    def test_clean_gcd_two_args(self):
        findings = run(self.rule, "import math\nmath.gcd(4, 6)")
        assert len(findings) == 0

    def test_suggestion_mentions_reduce(self):
        findings = run(self.rule, "math.gcd(4, 6, 8)")
        assert "reduce" in findings[0].suggestion.lower()