import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy052_free_threaded_threading_local import (
    FreeThreadedThreadingLocalRule,
)


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY052:
    rule = FreeThreadedThreadingLocalRule()

    def test_detects_threading_local(self):
        findings = run(self.rule,
            "import threading\nlocal = threading.local()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY052"
        assert findings[0].severity == Severity.INFO

    def test_clean_other_threading_call(self):
        findings = run(self.rule,
            "import threading\nt = threading.Thread()")
        assert len(findings) == 0

    def test_suggestion_mentions_nogil(self):
        findings = run(self.rule, "threading.local()")
        assert "nogil" in findings[0].suggestion.lower() or \
               "free" in findings[0].suggestion.lower() or \
               "lock" in findings[0].suggestion.lower()