import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY046:
    rule = OpenEncodingRule()

    def test_detects_open_without_encoding(self):
        findings = run(self.rule, "f = open('file.txt', 'r')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY046"
        assert findings[0].severity == Severity.WARNING

    def test_detects_open_write_without_encoding(self):
        findings = run(self.rule, "f = open('file.txt', 'w')")
        assert len(findings) == 1

    def test_clean_open_with_encoding(self):
        findings = run(self.rule, "f = open('file.txt', encoding='utf-8')")
        assert len(findings) == 0

    def test_clean_open_binary_mode(self):
        findings = run(self.rule, "f = open('file.txt', 'rb')")
        assert len(findings) == 0

    def test_suggestion_mentions_utf8(self):
        findings = run(self.rule, "open('file.txt')")
        assert "utf-8" in findings[0].suggestion.lower()