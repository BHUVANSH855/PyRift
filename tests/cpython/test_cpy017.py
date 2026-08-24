import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy017_unpack import UnpackRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY017:
    rule = UnpackRule()

    def test_detects_unpack_import(self):
        findings = run(self.rule, "from typing import Unpack")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY017"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Union")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import Unpack")
        assert "typing_extensions" in findings[0].suggestion.lower()