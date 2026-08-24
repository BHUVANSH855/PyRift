import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy027_locale_resetlocale import LocaleResetlocaleRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY027:
    rule = LocaleResetlocaleRule()

    def test_detects_resetlocale(self):
        findings = run(self.rule, "import locale\nlocale.resetlocale()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY027"
        assert findings[0].severity == Severity.ERROR

    def test_clean_setlocale(self):
        findings = run(self.rule,
            "import locale\nlocale.setlocale(locale.LC_ALL, '')")
        assert len(findings) == 0

    def test_suggestion_mentions_setlocale(self):
        findings = run(self.rule, "locale.resetlocale()")
        assert "setlocale" in findings[0].suggestion.lower()