import ast, textwrap
from pyrift.rules.pypy.ppy005_io_buffering import IoBufferingRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY005:
    rule = IoBufferingRule()

    def test_detects_write_mode_open(self):
        findings = run(self.rule, "f = open('file.txt', 'w')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY005"

    def test_detects_append_mode(self):
        findings = run(self.rule, "f = open('log.txt', 'a')")
        assert len(findings) == 1

    def test_clean_read_mode(self):
        findings = run(self.rule, "f = open('file.txt', 'r')")
        assert len(findings) == 0

    def test_suggestion_mentions_context_manager(self):
        findings = run(self.rule, "f = open('file.txt', 'w')")
        assert "with" in findings[0].suggestion.lower()