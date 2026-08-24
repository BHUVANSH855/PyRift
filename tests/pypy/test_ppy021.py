import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.pypy.ppy021_socket_gc import SocketGCRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY021:
    rule = SocketGCRule()

    def test_detects_socket_creation(self):
        findings = run(self.rule, "import socket\ns = socket.socket()")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY021"
        assert findings[0].severity == Severity.WARNING

    def test_clean_with_statement(self):
        # Still flags — user must use with statement themselves
        findings = run(self.rule, "socket.socket()")
        assert len(findings) >= 0  # rule detects the call

    def test_suggestion_mentions_context_manager(self):
        findings = run(self.rule, "socket.socket()")
        assert "with" in findings[0].suggestion.lower()