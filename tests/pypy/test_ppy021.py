import ast
import textwrap

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
        # Socket inside a `with` statement is already safe
        findings = run(self.rule,
            "import socket\nwith socket.socket() as s: pass")
        assert len(findings) == 0

    def test_suggestion_mentions_context_manager(self):
        findings = run(self.rule, "socket.socket()")
        assert "with" in findings[0].suggestion.lower()

    def test_clean_try_finally_close(self):
        # Socket in try/finally with .close() in finally is safe
        findings = run(self.rule, """\
            import socket
            s = socket.socket()
            try:
                pass
            finally:
                s.close()
        """)
        assert len(findings) == 0

    def test_clean_nested_context_manager(self):
        # Socket inside nested `with` block is safe
        findings = run(self.rule, """\
            import socket
            with socket.socket() as s:
                with open('x') as f:
                    pass
        """)
        assert len(findings) == 0

    def test_still_flags_bare_socket(self):
        # Bare socket creation with no cleanup is still flagged
        findings = run(self.rule, "import socket\ns = socket.socket()")
        assert len(findings) == 1

    def test_detects_socket_module_attr(self):
        # socket.socket() style (module.attribute)
        findings = run(self.rule, "import socket\ns = socket.socket()")
        assert len(findings) == 1

    def test_detects_from_socket_import(self):
        # from socket import socket; s = socket()
        findings = run(self.rule, "from socket import socket\ns = socket()")
        assert len(findings) == 1