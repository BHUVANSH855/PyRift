import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy026_typing_io_re import TypingIoReRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY026:
    rule = TypingIoReRule()

    def test_detects_typing_io(self):
        findings = run(self.rule, "from typing.io import IO")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY026"
        assert findings[0].severity == Severity.ERROR

    def test_detects_typing_re(self):
        findings = run(self.rule, "from typing.re import Pattern")
        assert len(findings) == 1

    def test_clean_typing_import(self):
        findings = run(self.rule, "from typing import IO, Pattern")
        assert len(findings) == 0

    def test_suggestion_mentions_typing(self):
        findings = run(self.rule, "from typing.io import IO")
        assert "typing" in findings[0].suggestion.lower()