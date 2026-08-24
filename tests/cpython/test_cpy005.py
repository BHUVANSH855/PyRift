import ast, textwrap
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

    def test_clean_if_else(self):
        findings = run(self.rule, "if command == 'quit': quit()")
        assert len(findings) == 0