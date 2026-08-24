import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy015_never import NeverRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY015:
    rule = NeverRule()

    def test_detects_never_import(self):
        findings = run(self.rule, "from typing import Never")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY015"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import NoReturn")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import Never")
        assert "typing_extensions" in findings[0].suggestion.lower()