import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy045_sys_settrace import SysSettraceRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY045:
    rule = SysSettraceRule()

    def test_detects_sys_settrace(self):
        findings = run(self.rule,
            "import sys\nsys.settrace(my_tracer)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY045"
        assert findings[0].severity == Severity.WARNING

    def test_clean_sys_gettrace(self):
        findings = run(self.rule,
            "import sys\nsys.gettrace()")
        assert len(findings) == 0

    def test_suggestion_mentions_vmprof(self):
        findings = run(self.rule, "sys.settrace(fn)")
        assert "vmprof" in findings[0].suggestion.lower()