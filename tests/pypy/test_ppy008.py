import ast, textwrap
from pyrift.rules.pypy.ppy008_threading_local import ThreadingLocalRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY008:
    rule = ThreadingLocalRule()

    def test_detects_threading_local(self):
        findings = run(self.rule, "import threading\nlocal = threading.local()")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY008"

    def test_clean_other_threading_call(self):
        findings = run(self.rule, "import threading\nt = threading.Thread()")
        assert len(findings) == 0

    def test_suggestion_mentions_cleanup(self):
        findings = run(self.rule, "threading.local()")
        assert "del" in findings[0].suggestion.lower() or \
               "clean" in findings[0].suggestion.lower()