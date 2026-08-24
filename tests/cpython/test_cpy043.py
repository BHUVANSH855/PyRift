import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy043_math_lcm import MathLcmRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY043:
    rule = MathLcmRule()

    def test_detects_math_lcm(self):
        findings = run(self.rule, "import math\nr = math.lcm(4, 6)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY043"
        assert findings[0].severity == Severity.ERROR

    def test_clean_math_gcd(self):
        findings = run(self.rule, "import math\nmath.gcd(4, 6)")
        assert len(findings) == 0

    def test_suggestion_mentions_gcd(self):
        findings = run(self.rule, "math.lcm(4, 6)")
        assert "gcd" in findings[0].suggestion.lower()