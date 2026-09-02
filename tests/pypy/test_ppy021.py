import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy021_socket_gc import SocketGCRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: SocketGCRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY021:
    rule = SocketGCRule()

    def test_detects_socket_creation(self):
        findings = run(
            self.rule,
            "import socket\ns = socket.socket()",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY021"
        assert findings[0].severity == Severity.WARNING

    def test_clean_direct_close(self):
        findings = run(
            self.rule,
            """
            import socket
            s = socket.socket()
            s.close()
            """,
        )

        assert len(findings) == 0

    def test_clean_close_inside_if(self):
        findings = run(
            self.rule,
            """
            import socket
            s = socket.socket()

            if condition:
                s.close()
            """,
        )

        assert len(findings) == 0

    def test_clean_close_inside_function(self):
        findings = run(
            self.rule,
            """
            import socket

            def use_socket():
                s = socket.socket()
                s.close()
            """,
        )

        assert len(findings) == 0

    def test_clean_close_inside_loop(self):
        findings = run(
            self.rule,
            """
            import socket

            s = socket.socket()

            for item in items:
                s.close()
            """,
        )

        assert len(findings) == 0

    def test_clean_close_inside_except(self):
        findings = run(
            self.rule,
            """
            import socket

            s = socket.socket()

            try:
                pass
            except Exception:
                s.close()
            """,
        )

        assert len(findings) == 0

    def test_clean_try_finally_close(self):
        findings = run(
            self.rule,
            """
            import socket

            s = socket.socket()

            try:
                pass
            finally:
                s.close()
            """,
        )

        assert len(findings) == 0

    def test_clean_with_statement(self):
        findings = run(
            self.rule,
            """
            import socket

            with socket.socket() as s:
                pass
            """,
        )

        assert len(findings) == 0

    def test_clean_nested_context_manager(self):
        findings = run(
            self.rule,
            """
            import socket

            with socket.socket() as s:
                with open("x") as f:
                    pass
            """,
        )

        assert len(findings) == 0

    def test_returned_socket_is_flagged(self):
        findings = run(
            self.rule,
            """
            import socket

            def make_socket():
                return socket.socket()
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY021"

    def test_socket_passed_to_function_is_flagged(self):
        findings = run(
            self.rule,
            """
            import socket

            s = socket.socket()
            use_socket(s)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY021"

    def test_unmanaged_socket_is_flagged(self):
        findings = run(
            self.rule,
            """
            import socket

            s = socket.socket()
            """,
        )

        assert len(findings) == 1

    def test_bare_socket_is_flagged(self):
        findings = run(
            self.rule,
            "socket.socket()",
        )

        assert len(findings) == 1

    def test_detects_from_socket_import(self):
        findings = run(
            self.rule,
            """
            from socket import socket

            s = socket()
            """,
        )

        assert len(findings) == 1

    def test_suggestion_mentions_explicit_cleanup(self):
        findings = run(
            self.rule,
            "socket.socket()",
        )

        assert len(findings) == 1
        suggestion = findings[0].suggestion.lower()
        assert "close" in suggestion
        assert "with" in suggestion