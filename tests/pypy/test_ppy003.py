import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.pypy.ppy003_getrefcount import GetRefcountRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY003:
    rule = GetRefcountRule()

    def test_detects_getrefcount(self):
        findings = run(self.rule, "import sys\nx = sys.getrefcount(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY003"
        assert findings[0].severity == Severity.ERROR

    def test_clean_sys_version(self):
        findings = run(self.rule, "import sys\nprint(sys.version)")
        assert len(findings) == 0

    def test_suggestion_mentions_gc(self):
        findings = run(self.rule, "sys.getrefcount(x)")
        assert "gc" in findings[0].suggestion.lower()