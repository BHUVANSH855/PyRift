import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy046_debug_constant import DebugConstantRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY046:
    rule = DebugConstantRule()

    def test_detects_if_debug(self):
        src = """
if __debug__:
    validate_state()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY046"
        assert findings[0].severity == Severity.WARNING

    def test_detects_if_not_debug(self):
        src = """
if not __debug__:
    skip_validation()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_assert_statement(self):
        src = "assert x > 0, 'x must be positive'"
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_env_var(self):
        src = "if __debug__:\n    check()"
        findings = run(self.rule, src)
        assert "env" in findings[0].suggestion.lower() or \
               "environ" in findings[0].suggestion.lower() or \
               "variable" in findings[0].suggestion.lower()