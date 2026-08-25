import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy038_decimal import DecimalBackendRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY038:
    rule = DecimalBackendRule()

    def test_detects_getcontext(self):
        findings = run(self.rule,
            "import decimal\ndecimal.getcontext().prec = 50")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY038"
        assert findings[0].severity == Severity.INFO

    def test_detects_setcontext(self):
        findings = run(self.rule,
            "import decimal\ndecimal.setcontext(ctx)")
        assert len(findings) == 1

    def test_clean_import_only(self):
        findings = run(self.rule, "import decimal")
        assert len(findings) == 0

    def test_clean_from_import(self):
        findings = run(self.rule, "from decimal import Decimal")
        assert len(findings) == 0

    def test_suggestion_mentions_test(self):
        findings = run(self.rule, "decimal.getcontext().prec = 28")
        assert "test" in findings[0].suggestion.lower() or \
               "pypy" in findings[0].suggestion.lower()