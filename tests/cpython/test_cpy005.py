import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy005_match_case import MatchCaseRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY005:
    rule = MatchCaseRule()

    def test_detects_match_statement(self):
        src = """
match command:
    case "quit":
        quit()
    case "go":
        go()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY005"
        assert findings[0].severity == Severity.ERROR

    def test_detects_match_with_wildcard(self):
        """match/case with a wildcard arm is still a match statement."""
        src = """
match status:
    case 200:
        pass
    case _:
        pass
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY005"

    def test_detects_nested_match(self):
        """Two match statements in one file → two findings."""
        src = """
match x:
    case 1:
        match y:
            case 2:
                pass
"""
        findings = run(self.rule, src)
        assert len(findings) == 2

    def test_detects_match_with_guard(self):
        """match/case with an if-guard is still flagged."""
        src = """
match point:
    case (x, y) if x > 0:
        pass
"""
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_if_else(self):
        findings = run(self.rule, "if command == 'quit': quit()")
        assert len(findings) == 0

    def test_clean_variable_named_match(self):
        """A variable or function called 'match' must not be flagged."""
        findings = run(self.rule, "match = re.match(r'\\d+', s)")
        assert len(findings) == 0