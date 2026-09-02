import ast
import textwrap

from pyrift.finding import Runtime, Severity
from pyrift.rules.pypy.ppy005_io_buffering import IoBufferingRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: IoBufferingRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY005:
    rule = IoBufferingRule()

    def test_detects_write_mode_open(self):
        findings = run(
            self.rule,
            "f = open('file.txt', 'w')",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY005"
        assert findings[0].runtime == Runtime.PYPY
        assert findings[0].severity == Severity.WARNING

    def test_detects_append_mode(self):
        findings = run(
            self.rule,
            "f = open('log.txt', 'a')",
        )

        assert len(findings) == 1

    def test_detects_exclusive_mode(self):
        findings = run(
            self.rule,
            "f = open('file.txt', 'x')",
        )

        assert len(findings) == 1

    def test_detects_read_write_mode(self):
        for mode in ("r+", "w+", "a+"):
            findings = run(
                self.rule,
                f"f = open('file.txt', '{mode}')",
            )

            assert len(findings) == 1, mode

    def test_detects_keyword_write_mode(self):
        findings = run(
            self.rule,
            "f = open('file.txt', mode='w')",
        )

        assert len(findings) == 1

    def test_detects_io_open_write_mode(self):
        findings = run(
            self.rule,
            "import io\nf = io.open('file.txt', 'w')",
        )

        assert len(findings) == 1

    def test_detects_builtins_open_write_mode(self):
        findings = run(
            self.rule,
            "import builtins\nf = builtins.open('file.txt', 'w')",
        )

        assert len(findings) == 1

    def test_clean_read_mode(self):
        findings = run(
            self.rule,
            "f = open('file.txt', 'r')",
        )

        assert len(findings) == 0

    def test_clean_binary_read_mode(self):
        findings = run(
            self.rule,
            "f = open('file.txt', 'rb')",
        )

        assert len(findings) == 0

    def test_context_manager_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            with open("file.txt", "w") as f:
                f.write("hello")
            """,
        )

        assert len(findings) == 0

    def test_context_manager_with_keyword_mode_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            with open("file.txt", mode="w") as f:
                f.write("hello")
            """,
        )

        assert len(findings) == 0

    def test_explicit_close_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            f = open("file.txt", "w")
            f.write("hello")
            f.close()
            """,
        )

        assert len(findings) == 0

    def test_explicit_close_inside_function_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            def write_file():
                f = open("file.txt", "w")
                f.write("hello")
                f.close()
            """,
        )

        assert len(findings) == 0

    def test_explicit_close_inside_if_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            f = open("file.txt", "w")
            if condition:
                f.close()
            """,
        )

        assert len(findings) == 0

    def test_explicit_close_inside_loop_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            f = open("file.txt", "w")
            for item in items:
                f.close()
            """,
        )

        assert len(findings) == 0

    def test_close_before_open_does_not_count(self):
        findings = run(
            self.rule,
            """
            f.close()
            f = open("file.txt", "w")
            """,
        )

        assert len(findings) == 1

    def test_unrelated_close_does_not_count(self):
        findings = run(
            self.rule,
            """
            f = open("file.txt", "w")
            other.close()
            """,
        )

        assert len(findings) == 1

    def test_close_of_different_variable_does_not_count(self):
        findings = run(
            self.rule,
            """
            f = open("file.txt", "w")
            other = open("other.txt", "w")
            other.close()
            """,
        )

        assert len(findings) == 1

    def test_close_in_nested_function_does_not_count(self):
        findings = run(
            self.rule,
            """
            def write_file():
                f = open("file.txt", "w")

                def cleanup():
                    f.close()
            """,
        )

        assert len(findings) == 1

    def test_annotated_assignment_with_close_is_clean(self):
        findings = run(
            self.rule,
            """
            f: object = open("file.txt", "w")
            f.close()
            """,
        )

        assert len(findings) == 0

    def test_suggestion_mentions_context_manager_and_close(self):
        findings = run(
            self.rule,
            "f = open('file.txt', 'w')",
        )

        suggestion = findings[0].suggestion.lower()

        assert "with" in suggestion
        assert "close" in suggestion

    def test_unrelated_open_call_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            class Factory:
                def open(self, path, mode):
                    return object()

            factory = Factory()
            f = factory.open("file.txt", "w")
            """,
        )

        assert len(findings) == 0