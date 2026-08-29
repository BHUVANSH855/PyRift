"""
Tests for version-guard awareness.

Verifies that imports inside ``if sys.version_info >= (x, y):`` blocks
that already cover the required version are NOT flagged by rules.
"""
from __future__ import annotations

import ast
import textwrap


def _parse(src: str) -> ast.Module:
    return ast.parse(textwrap.dedent(src))


def _run_rule(rule_class, src: str, target_config=None):
    tree = _parse(src)
    rule = rule_class()
    return rule.check(tree, "<test>", target_config)


class TestVersionGuardAwareness:
    """Version-guarded imports should not produce false positives."""

    def test_cpy004_tomllib_guarded_311(self):
        """tomllib guarded by sys.version_info >= (3, 11) should not fire."""
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
        import sys
        if sys.version_info >= (3, 11):
            import tomllib
        """
        findings = _run_rule(TomllibRule, src)
        assert len(findings) == 0

    def test_cpy004_tomllib_unguarded(self):
        """tomllib without guard should fire."""
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
        import tomllib
        """
        findings = _run_rule(TomllibRule, src)
        assert len(findings) == 1

    def test_cpy009_exception_group_guarded_311(self):
        """ExceptionGroup guarded by sys.version_info >= (3, 11) should not fire."""
        from pyrift.rules.cpython.cpy009_exception_group import ExceptionGroupRule
        src = """
        import sys
        if sys.version_info >= (3, 11):
            from exceptiongroup import ExceptionGroup
        """
        findings = _run_rule(ExceptionGroupRule, src)
        assert len(findings) == 0

    def test_cpy011_typing_self_guarded_311(self):
        """typing.Self guarded by sys.version_info >= (3, 11) should not fire."""
        from pyrift.rules.cpython.cpy011_typing_self import TypingSelfRule
        src = """
        import sys
        if sys.version_info >= (3, 11):
            from typing import Self
        """
        findings = _run_rule(TypingSelfRule, src)
        assert len(findings) == 0

    def test_cpy019_distutils_guarded_312(self):
        """distutils guarded by sys.version_info < (3, 12) still fires.

        The version-guard system only recognizes >= and > operators.
        A < guard is not recognized as protective, so the rule still reports.
        """
        from pyrift.rules.cpython.cpy019_distutils import DistutilsRule
        src = """
        import sys
        if sys.version_info < (3, 12):
            from distutils.core import setup
        """
        findings = _run_rule(DistutilsRule, src)
        assert len(findings) == 1

    def test_cpy003_union_type_guarded_310(self):
        """X | Y union syntax guarded by sys.version_info >= (3, 10) should not fire."""
        from pyrift.rules.cpython.cpy003_union_type_syntax import UnionTypeSyntaxRule
        src = """
        import sys
        if sys.version_info >= (3, 10):
            def foo(x: int | str) -> None:
                pass
        """
        findings = _run_rule(UnionTypeSyntaxRule, src)
        assert len(findings) == 0

    def test_cpy005_match_case_no_guard_support(self):
        """match/case is a syntax feature - version guards don't help (syntax error on parse)."""
        from pyrift.rules.cpython.cpy005_match_case import MatchCaseRule
        src = """
        import sys
        if sys.version_info >= (3, 10):
            match x:
                case 1:
                    pass
        """
        # match/case rule doesn't use version-guard awareness because
        # on Python < 3.10 this wouldn't even parse (SyntaxError).
        # The rule correctly fires to warn about version compatibility.
        findings = _run_rule(MatchCaseRule, src)
        assert len(findings) == 1

    def test_cpy020_datetime_utc_guarded_311(self):
        """datetime.UTC guarded by sys.version_info >= (3, 11) should not fire."""
        from pyrift.rules.cpython.cpy020_datetime_utc import DatetimeUTCRule
        src = """
        import sys
        if sys.version_info >= (3, 11):
            from datetime import timezone
            utc = timezone.utc
        """
        findings = _run_rule(DatetimeUTCRule, src)
        assert len(findings) == 0

    def test_guard_with_gt_operator(self):
        """sys.version_info > (3, 10) should also be recognized as a guard."""
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
        import sys
        if sys.version_info > (3, 10):
            import tomllib
        """
        findings = _run_rule(TomllibRule, src)
        assert len(findings) == 0

    def test_guard_inside_function(self):
        """Version guard inside a function should still suppress the finding."""
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
        import sys

        def load_config():
            if sys.version_info >= (3, 11):
                import tomllib
                return tomllib.load
            else:
                import toml
                return toml.load
        """
        findings = _run_rule(TomllibRule, src)
        assert len(findings) == 0

    def test_guard_with_tuple_comparison_version_tuple(self):
        """Guard comparing only major version tuple (3,) is not recognized."""
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
        import sys
        if sys.version_info >= (3,):
            import tomllib
        """
        findings = _run_rule(TomllibRule, src)
        # A 1-element tuple guard is not recognized, so the rule still fires.
        assert len(findings) == 1

    def test_unguarded_import_with_version_info_in_file(self):
        """version_info used elsewhere does not suppress unguarded import."""
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
        import sys
        print(sys.version_info)
        import tomllib
        """
        findings = _run_rule(TomllibRule, src)
        assert len(findings) == 1

    def test_guard_with_else_branch_import(self):
        """Both if and else branch imports are considered guarded.

        The version-guard system walks up the AST and finds the parent If
        node from both branches, so both imports are suppressed.
        """
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
        import sys
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomllib
        """
        findings = _run_rule(TomllibRule, src)
        # Both branches share the same parent If with the version guard,
        # so both imports are considered guarded.
        assert len(findings) == 0
