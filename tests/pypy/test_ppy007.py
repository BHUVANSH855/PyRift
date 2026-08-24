import ast, textwrap
from pyrift.rules.pypy.ppy007_sys_intern import SysInternRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY007:
    rule = SysInternRule()

    def test_detects_sys_intern(self):
        findings = run(self.rule, "import sys\ns = sys.intern('hello')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY007"

    def test_clean_sys_version(self):
        findings = run(self.rule, "import sys\nprint(sys.version)")
        assert len(findings) == 0

    def test_suggestion_mentions_equality(self):
        findings = run(self.rule, "sys.intern('x')")
        assert "==" in findings[0].suggestion