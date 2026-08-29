import ast
import textwrap

from pyrift.rules.pypy.ppy026_builtins_module import BuiltinsModuleRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY026:
    rule = BuiltinsModuleRule()

    def test_detects_builtins_access(self):
        findings = run(self.rule, "x = __builtins__")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY026"

    def test_detects_builtins_isinstance(self):
        # isinstance(__builtins__, dict) IS the canonical pattern to flag
        findings = run(self.rule,
            "if isinstance(__builtins__, dict): pass")
        assert len(findings) == 1

    def test_suggestion_mentions_builtins_module(self):
        findings = run(self.rule, "__builtins__")
        assert "builtins" in findings[0].suggestion.lower()

    def test_clean_version_guard(self):
        # __builtins__ inside a sys.version_info guard is intentional compat code
        findings = run(self.rule, """\
            import sys
            if sys.version_info >= (3, 10):
                x = __builtins__
            else:
                x = __builtins__
        """)
        assert len(findings) == 0

    def test_clean_isinstance_check(self):
        # isinstance(__builtins__, dict) is the exact pattern that differs on PyPy
        findings = run(self.rule,
            "if isinstance(__builtins__, dict):\n    pass")
        assert len(findings) == 1

    def test_clean_compat_shim(self):
        # from __builtins__ import * — ImportFrom node, not Name node
        # so the rule doesn't detect it (ImportFrom is not __builtins__ access)
        findings = run(self.rule, "from __builtins__ import *")
        assert len(findings) == 0

    def test_still_flags_direct_access(self):
        # Direct attribute access on __builtins__ should still be flagged
        findings = run(self.rule, "x = __builtins__.print")
        assert len(findings) == 1

    def test_still_flags_dict_access(self):
        # __builtins__['name'] should still be flagged
        findings = run(self.rule, "x = __builtins__['print']")
        assert len(findings) == 1