import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.pypy.ppy013_getsizeof import GetSizeofRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY013:
    rule = GetSizeofRule()

    def test_detects_getsizeof(self):
        findings = run(self.rule, "import sys\nsize = sys.getsizeof(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY013"
        assert findings[0].severity == Severity.ERROR

    def test_clean_sys_version(self):
        findings = run(self.rule, "import sys\nprint(sys.version)")
        assert len(findings) == 0

    def test_suggestion_mentions_vmprof(self):
        findings = run(self.rule, "sys.getsizeof(x)")
        assert "vmprof" in findings[0].suggestion.lower() or \
               "pypy" in findings[0].suggestion.lower()