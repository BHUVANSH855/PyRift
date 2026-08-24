import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.pypy.ppy024_timeit import TimeitRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY024:
    rule = TimeitRule()

    def test_detects_import_timeit(self):
        findings = run(self.rule, "import timeit")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY024"
        assert findings[0].severity == Severity.INFO

    def test_detects_from_import_timeit(self):
        findings = run(self.rule, "from timeit import timeit")
        assert len(findings) == 1

    def test_clean_other_import(self):
        findings = run(self.rule, "import time")
        assert len(findings) == 0

    def test_suggestion_mentions_jit(self):
        findings = run(self.rule, "import timeit")
        assert "jit" in findings[0].suggestion.lower() or \
               "warmup" in findings[0].suggestion.lower() or \
               "iterations" in findings[0].suggestion.lower()