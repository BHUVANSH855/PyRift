import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy025_paramspec import ParamSpecRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY025:
    rule = ParamSpecRule()

    def test_detects_paramspec_import(self):
        findings = run(self.rule, "from typing import ParamSpec")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY025"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import TypeVar")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import ParamSpec")
        assert "typing_extensions" in findings[0].suggestion.lower()