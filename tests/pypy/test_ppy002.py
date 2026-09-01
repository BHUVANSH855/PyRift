import ast
import textwrap

from pyrift.rules.pypy.ppy002_ctypes import CtypesRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: CtypesRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY002:
    rule = CtypesRule()

    def test_detects_ctypes_cdll(self):
        findings = run(
            self.rule,
            "import ctypes\nlib = ctypes.CDLL('libfoo.so')",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY002"

    def test_detects_ctypes_cast(self):
        findings = run(
            self.rule,
            "import ctypes\nvalue = ctypes.cast(ptr, ctypes.c_void_p)",
        )

        assert len(findings) == 1

    def test_detects_ctypes_structure(self):
        findings = run(
            self.rule,
            """
            import ctypes

            class Header(ctypes.Structure):
                _fields_ = []
            """,
        )

        assert len(findings) == 1

    def test_detects_direct_import(self):
        findings = run(
            self.rule,
            """
            from ctypes import CDLL

            lib = CDLL("libfoo.so")
            """,
        )

        assert len(findings) == 1

    def test_detects_aliased_direct_import(self):
        findings = run(
            self.rule,
            """
            from ctypes import CDLL as load_library

            lib = load_library("libfoo.so")
            """,
        )

        assert len(findings) == 1

    def test_no_finding_without_ctypes_import(self):
        findings = run(
            self.rule,
            "x = CDLL('foo')",
        )

        assert len(findings) == 0

    def test_does_not_flag_unrelated_attribute(self):
        findings = run(
            self.rule,
            """
            import ctypes

            something = object()
            value = something.cast()
            """,
        )

        assert len(findings) == 0

    def test_does_not_flag_unrelated_same_named_call(self):
        findings = run(
            self.rule,
            """
            import ctypes

            def cast(value):
                return value

            result = cast(value)
            """,
        )

        assert len(findings) == 0

    def test_does_not_flag_other_ctypes_api(self):
        findings = run(
            self.rule,
            """
            import ctypes

            value = ctypes.c_int(1)
            """,
        )

        assert len(findings) == 0

    def test_suggestion_mentions_cffi(self):
        findings = run(
            self.rule,
            "import ctypes\nctypes.cast(ptr, ctypes.c_void_p)",
        )

        assert "cffi" in findings[0].suggestion.lower()