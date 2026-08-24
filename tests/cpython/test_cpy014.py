import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy014_type_alias import TypeAliasRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY014:
    rule = TypeAliasRule()

    def test_detects_type_alias_import(self):
        findings = run(self.rule, "from typing import TypeAlias")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY014"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Optional")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import TypeAlias")
        assert "typing_extensions" in findings[0].suggestion.lower()