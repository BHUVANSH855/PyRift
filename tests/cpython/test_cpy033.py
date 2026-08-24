import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy033_is_relative_to import IsRelativeToRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY033:
    rule = IsRelativeToRule()

    def test_detects_is_relative_to(self):
        findings = run(self.rule,
            "from pathlib import Path\np.is_relative_to('/base')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY033"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_pathlib_method(self):
        findings = run(self.rule, "p.is_absolute()")
        assert len(findings) == 0

    def test_suggestion_mentions_relative_to(self):
        findings = run(self.rule, "p.is_relative_to('/x')")
        assert "relative_to" in findings[0].suggestion.lower()