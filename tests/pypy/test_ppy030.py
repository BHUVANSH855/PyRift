import ast, textwrap
from pyrift.rules.pypy.ppy030_sys_flags import SysFlagsRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY030:
    rule = SysFlagsRule()

    def test_detects_sys_flags_hash_randomization(self):
        findings = run(self.rule,
            "import sys\nx = sys.flags.hash_randomization")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY030"

    def test_detects_sys_flags_ignore_environment(self):
        findings = run(self.rule,
            "import sys\nx = sys.flags.ignore_environment")
        assert len(findings) == 1

    def test_clean_other_sys_flags(self):
        findings = run(self.rule,
            "import sys\nx = sys.flags.debug")
        assert len(findings) == 0

    def test_suggestion_mentions_test(self):
        findings = run(self.rule, "sys.flags.hash_randomization")
        assert "test" in findings[0].suggestion.lower() or \
               "pypy" in findings[0].suggestion.lower()