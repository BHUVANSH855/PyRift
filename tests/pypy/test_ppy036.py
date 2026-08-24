import ast
import textwrap

from pyrift.rules.pypy.ppy036_open_flush import OpenFlushRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY036:
    rule = OpenFlushRule()

    def test_detects_line_buffering(self):
        findings = run(self.rule, "f = open('file.txt', 'w', buffering=1)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY036"

    def test_clean_default_buffering(self):
        findings = run(self.rule, "f = open('file.txt', 'w')")
        assert len(findings) == 0

    def test_clean_full_buffering(self):
        findings = run(self.rule, "f = open('file.txt', 'w', buffering=8192)")
        assert len(findings) == 0

    def test_suggestion_mentions_flush(self):
        findings = run(self.rule, "open('f', 'w', buffering=1)")
        assert "flush" in findings[0].suggestion.lower()