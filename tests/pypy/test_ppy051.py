import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy051_co_lnotab import CoLnotabPyPyRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY051:
    rule = CoLnotabPyPyRule()

    def test_detects_lnotab(self):
        findings = run(self.rule, "code_obj.__lnotab__")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY051"
        assert findings[0].severity == Severity.WARNING

    def test_clean_co_lines(self):
        findings = run(self.rule, "code_obj.co_lines()")
        assert len(findings) == 0

    def test_clean_co_linetable(self):
        findings = run(self.rule, "code_obj.co_linetable()")
        assert len(findings) == 0
