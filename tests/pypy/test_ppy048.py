import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy048_sys_getsizeof import SysGetsizeofRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY048:
    rule = SysGetsizeofRule()

    def test_detects_getsizeof(self):
        findings = run(self.rule, "import sys\nsys.getsizeof(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY048"
        assert findings[0].severity == Severity.WARNING

    def test_clean_getrefcount(self):
        findings = run(self.rule, "import sys\nsys.getrefcount(obj)")
        assert len(findings) == 0

    def test_clean_other_module(self):
        findings = run(self.rule, "import os\nos.getsizeof(obj)")
        assert len(findings) == 0

    def test_suggestion_mentions_relative(self):
        findings = run(self.rule, "import sys\nsys.getsizeof(obj)")
        assert "relative" in findings[0].suggestion.lower() or "comparison" in findings[0].suggestion.lower()
