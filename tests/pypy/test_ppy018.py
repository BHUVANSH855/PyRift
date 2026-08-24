import ast, textwrap
from pyrift.rules.pypy.ppy018_recursion_limit import RecursionLimitRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY018:
    rule = RecursionLimitRule()

    def test_detects_setrecursionlimit(self):
        findings = run(self.rule, "import sys\nsys.setrecursionlimit(10000)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY018"

    def test_clean_sys_version(self):
        findings = run(self.rule, "sys.getrecursionlimit()")
        assert len(findings) == 0

    def test_suggestion_mentions_iteration(self):
        findings = run(self.rule, "sys.setrecursionlimit(5000)")
        assert "iteration" in findings[0].suggestion.lower() or \
               "higher" in findings[0].suggestion.lower()