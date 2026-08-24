import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy029_locals_behaviour import LocalsBehaviourRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY029:
    rule = LocalsBehaviourRule()

    def test_detects_locals_call(self):
        findings = run(self.rule, "d = locals()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY029"
        assert findings[0].severity == Severity.WARNING

    def test_suggestion_mentions_dict(self):
        findings = run(self.rule, "locals()")
        assert "dict" in findings[0].suggestion.lower()