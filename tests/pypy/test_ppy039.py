import ast
import textwrap

from pyrift.rules.pypy.ppy039_os_fork import OsForkRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY039:
    rule = OsForkRule()

    def test_detects_os_fork(self):
        findings = run(self.rule, "import os\npid = os.fork()")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY039"

    def test_clean_os_getpid(self):
        findings = run(self.rule, "import os\nos.getpid()")
        assert len(findings) == 0

    def test_suggestion_mentions_multiprocessing(self):
        findings = run(self.rule, "os.fork()")
        assert "multiprocessing" in findings[0].suggestion.lower()