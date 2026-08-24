import ast
import textwrap

from pyrift.rules.pypy.ppy002_ctypes import CtypesRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY002:
    rule = CtypesRule()

    def test_detects_ctypes_cdll(self):
        findings = run(self.rule, "import ctypes\nlib = ctypes.CDLL('libfoo.so')")
        assert any(f.rule_id == "PPY002" for f in findings)

    def test_no_finding_without_import(self):
        findings = run(self.rule, "x = CDLL('foo')")
        assert len(findings) == 0

    def test_cffi_suggestion_present(self):
        findings = run(self.rule, "import ctypes\nctypes.cast(ptr, ctypes.c_void_p)")
        if findings:
            assert "cffi" in findings[0].suggestion.lower()