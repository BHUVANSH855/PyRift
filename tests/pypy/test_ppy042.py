import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy042_print_flush import PrintFlushRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY042:
    rule = PrintFlushRule()

    def test_detects_print_flush_true(self):
        findings = run(self.rule, "print('hello', flush=True)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY042"
        assert findings[0].severity == Severity.INFO

    def test_clean_print_no_flush(self):
        findings = run(self.rule, "print('hello')")
        assert len(findings) == 0

    def test_clean_print_flush_false(self):
        findings = run(self.rule, "print('hello', flush=False)")
        assert len(findings) == 0

    def test_suggestion_mentions_sys_stdout(self):
        findings = run(self.rule, "print('x', flush=True)")
        assert "sys.stdout" in findings[0].suggestion.lower() or \
               "flush" in findings[0].suggestion.lower()