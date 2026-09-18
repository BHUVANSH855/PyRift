"""
Tests for pyrift.analysis.guards and its integration into the scanner
as a project-wide false-positive filter (2026-09 review, points 73-78).
"""

from __future__ import annotations

import ast
import textwrap

from pyrift.analysis.guards import build_guard_index, guard_reduces_risk
from pyrift.scanner import scan_file


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


class TestVersionGuards:
    def test_min_version_guard_detected(self):
        tree = parse(
            """
            import sys
            if sys.version_info >= (3, 11):
                from typing import Self
            """
        )
        index = build_guard_index(tree)
        # line 4 is the `from typing import Self` statement
        guard = index.version_guard_at(4)
        assert guard is not None
        assert guard.min_version == (3, 11)

    def test_max_version_guard_detected_in_else_branch(self):
        tree = parse(
            """
            import sys
            if sys.version_info >= (3, 11):
                from typing import Self
            else:
                from typing_extensions import Self
            """
        )
        index = build_guard_index(tree)
        guard = index.version_guard_at(6)  # the else branch
        assert guard is not None
        assert guard.max_version == (3, 11)

    def test_less_than_guard(self):
        tree = parse(
            """
            import sys
            if sys.version_info < (3, 13):
                x = old_api()
            """
        )
        index = build_guard_index(tree)
        guard = index.version_guard_at(4)
        assert guard is not None
        assert guard.max_version == (3, 13)

    def test_no_guard_outside_if_block(self):
        tree = parse("from typing import Self")
        index = build_guard_index(tree)
        assert index.version_guard_at(1) is None


class TestImplementationGuards:
    def test_pypy_only_branch_detected(self):
        tree = parse(
            """
            import sys
            if sys.implementation.name == "pypy":
                do_pypy_thing()
            """
        )
        index = build_guard_index(tree)
        assert index.is_pypy_only(4)
        assert not index.is_cpython_only(4)

    def test_cpython_only_else_branch_detected(self):
        tree = parse(
            """
            import sys
            if sys.implementation.name == "pypy":
                do_pypy_thing()
            else:
                do_cpython_thing()
            """
        )
        index = build_guard_index(tree)
        assert index.is_cpython_only(6)

    def test_platform_python_implementation_check(self):
        tree = parse(
            """
            import platform
            if platform.python_implementation() == "PyPy":
                do_pypy_thing()
            """
        )
        index = build_guard_index(tree)
        assert index.is_pypy_only(4)

    def test_not_pypy_check(self):
        tree = parse(
            """
            import sys
            if sys.implementation.name != "pypy":
                do_cpython_thing()
            """
        )
        index = build_guard_index(tree)
        assert index.is_cpython_only(4)


class TestImportShims:
    def test_try_except_import_error_marks_both_branches(self):
        tree = parse(
            """
            try:
                from typing import Self
            except ImportError:
                from typing_extensions import Self
            """
        )
        index = build_guard_index(tree)
        assert index.is_import_shim(3)  # try body
        assert index.is_import_shim(5)  # except body

    def test_bare_except_counts_as_shim(self):
        tree = parse(
            """
            try:
                from typing import Self
            except:
                from typing_extensions import Self
            """
        )
        index = build_guard_index(tree)
        assert index.is_import_shim(3)

    def test_non_import_exception_type_does_not_count_as_shim(self):
        # Only ImportError/ModuleNotFoundError/bare-except are treated
        # as compatibility shims -- an arbitrary `except Exception:` is
        # not evidence of an import-fallback pattern.
        tree = parse(
            """
            try:
                risky_call()
            except Exception:
                fallback()
            """
        )
        index = build_guard_index(tree)
        assert not index.is_import_shim(3)

    def test_unrelated_statement_inside_import_shim_is_not_marked(self):
        tree = parse(
            """
            try:
                from optional_package import feature
                compatibility_sensitive_call()
            except ImportError:
                from fallback_package import feature
            """
        )
        index = build_guard_index(tree)

        # The import itself is part of the compatibility shim.
        assert index.is_import_shim(3)

        # The unrelated call must remain visible to compatibility rules.
        assert not index.is_import_shim(4)

        # The fallback import is also part of the shim.
        assert index.is_import_shim(6)

    def test_non_import_try_statement_remains_visible_to_guard_filter(self):
        tree = parse(
            """
            try:
                import optional_package
                value = compatibility_sensitive_call()
            except ImportError:
                import fallback_package
            """
        )
        index = build_guard_index(tree)

        assert index.is_import_shim(3)
        assert not index.is_import_shim(4)
        assert index.is_import_shim(6)


class TestTypeChecking:
    def test_type_checking_block_detected(self):
        tree = parse(
            """
            from typing import TYPE_CHECKING
            if TYPE_CHECKING:
                from typing import Self
            """
        )
        index = build_guard_index(tree)
        assert index.is_type_checking_only(4)


class TestGuardReducesRisk:
    def test_compatibility_finding_suppressed_by_satisfying_version_guard(self):
        # Real rules (e.g. CPY011, CPY030) encode "requires Python X+" as
        # affected_from="<earliest broken version>",
        # affected_until="<version just before the fix/requirement>" --
        # i.e. the *window during which the code is broken*, not the
        # version that introduces the API. A guard of `>= 3.11` makes the
        # guarded branch run only where the API is actually available
        # (outside the broken window [3.0, 3.11)), so it should suppress.
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 11):
                    from typing import Self
                """
            )
        )
        should_suppress, reason = guard_reduces_risk(
            index,
            4,
            finding_runtime="cpython",
            affected_from="3.0",
            affected_until="3.11",
            category="compatibility",
        )
        assert should_suppress
        assert "version_info" in reason

    def test_compatibility_finding_not_suppressed_when_affected_forever_after_guard(self):
        # P0 regression (2026-09 audit): a guard of `>= affected_from`
        # must NOT suppress a finding whose affected window starts at
        # (or before) the guard's own lower bound and has no upper bound
        # -- the guarded branch runs squarely inside the affected range.
        # This is the exact bug reported against CPY047
        # (collections.abc.ByteString, affected [3.15, 3.17)).
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 15):
                    from collections.abc import ByteString
                """
            )
        )
        should_suppress, _reason = guard_reduces_risk(
            index,
            4,
            finding_runtime="cpython",
            affected_from="3.15",
            affected_until="3.17",
            category="compatibility",
        )
        assert not should_suppress

    def test_compatibility_finding_not_suppressed_when_guard_fully_inside_unbounded_range(self):
        # affected_from set, no affected_until => affected "forever from
        # that point on". A guard whose lower bound is >= affected_from
        # still runs entirely inside the affected range and must not be
        # suppressed.
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 14):
                    import something_removed_in_3_14
                """
            )
        )
        should_suppress, _reason = guard_reduces_risk(
            index,
            4,
            finding_runtime="cpython",
            affected_from="3.14",
            affected_until="",
            category="compatibility",
        )
        assert not should_suppress

    def test_compatibility_finding_not_suppressed_when_guard_insufficient(self):
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 9):
                    from typing import Self
                """
            )
        )
        # Guard only proves >=3.9, but Self needs >=3.11 -- must NOT suppress.
        should_suppress, _ = guard_reduces_risk(
            index,
            4,
            finding_runtime="cpython",
            affected_from="3.11",
            affected_until="",
            category="compatibility",
        )
        assert not should_suppress

    def test_older_else_branch_suppressed_for_future_api(self):
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 11):
                    from typing import Self
                else:
                    from typing_extensions import Self
                """
            )
        )
        # The else branch only runs before 3.11. Using the real-rule
        # encoding, the API requirement is expressed as a broken window
        # of [3.0, 3.11) -- and the else branch (< 3.11) runs entirely
        # *inside* that broken window, so it must NOT be suppressed: the
        # else branch is exactly the code path that needs the shim.
        should_suppress, _reason = guard_reduces_risk(
            index,
            6,
            finding_runtime="cpython",
            affected_from="3.0",
            affected_until="3.11",
            category="compatibility",
        )
        assert not should_suppress

    def test_earlier_branch_suppressed_when_guard_runs_before_affected_window(self):
        # A guard that runs strictly before the affected window starts
        # (disjoint, guard fully "to the left") is correctly suppressed.
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info < (3, 12):
                    from distutils import setup
                """
            )
        )
        should_suppress, reason = guard_reduces_risk(
            index,
            4,
            finding_runtime="cpython",
            affected_from="3.12",
            affected_until="",
            category="compatibility",
        )
        assert should_suppress
        assert "before the affected version range" in reason

    def test_older_else_branch_not_suppressed_for_preexisting_api(self):
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 11):
                    from typing import Self
                else:
                    from typing_extensions import Self
                """
            )
        )
        # An API that already existed before the guard's cutoff remains
        # relevant in the else branch.
        should_suppress, _ = guard_reduces_risk(
            index,
            6,
            finding_runtime="cpython",
            affected_from="3.10",
            affected_until="",
            category="compatibility",
        )
        assert not should_suppress

    def test_semantic_finding_not_suppressed_by_shim(self):
        # Shims only neutralise API-availability (compatibility) risk,
        # never a genuine silent semantic difference.
        index = build_guard_index(
            parse(
                """
                try:
                    import pickle
                except ImportError:
                    pass
                pickle.dumps(x)
                """
            )
        )
        should_suppress, _ = guard_reduces_risk(
            index,
            2,
            finding_runtime="cpython",
            affected_from="",
            affected_until="",
            category="semantic",
        )
        assert not should_suppress

    def test_type_checking_downgrades_not_suppresses(self):
        index = build_guard_index(
            parse(
                """
                from typing import TYPE_CHECKING
                if TYPE_CHECKING:
                    from typing import Self
                """
            )
        )
        should_suppress, reason = guard_reduces_risk(
            index,
            4,
            finding_runtime="cpython",
            affected_from="3.11",
            affected_until="",
            category="compatibility",
        )
        assert not should_suppress
        assert reason  # a downgrade reason is still returned


class TestScannerIntegration:
    def test_version_guarded_typing_self_is_suppressed_end_to_end(self, tmp_path):
        f = tmp_path / "shim.py"
        f.write_text(
            textwrap.dedent(
                """
                import sys
                if sys.version_info >= (3, 11):
                    from typing import Self
                else:
                    from typing_extensions import Self
                """
            )
        )
        findings = scan_file(f)
        assert not any(fi.rule_id == "CPY011" for fi in findings)

    def test_version_guarded_distutils_is_suppressed_end_to_end(
        self,
        tmp_path,
    ):
        f = tmp_path / "distutils_guarded.py"
        f.write_text(
            textwrap.dedent(
                """
                import sys
                if sys.version_info < (3, 12):
                    import distutils
                """
            )
        )
        findings = scan_file(f)
        assert not any(fi.rule_id == "CPY019" for fi in findings)

    def test_insufficient_version_guard_does_not_suppress_distutils(
        self,
        tmp_path,
    ):
        f = tmp_path / "distutils_insufficient_guard.py"
        f.write_text(
            textwrap.dedent(
                """
                import sys
                if sys.version_info >= (3, 11):
                    import distutils
                """
            )
        )
        findings = scan_file(f)
        assert any(fi.rule_id == "CPY019" for fi in findings)

    def test_try_except_shim_is_suppressed_end_to_end(self, tmp_path):
        f = tmp_path / "shim.py"
        f.write_text(
            textwrap.dedent(
                """
                try:
                    from typing import Self
                except ImportError:
                    from typing_extensions import Self
                """
            )
        )
        findings = scan_file(f)
        assert not any(fi.rule_id == "CPY011" for fi in findings)

    def test_unguarded_typing_self_still_flagged(self, tmp_path):
        f = tmp_path / "unguarded.py"
        f.write_text("from typing import Self\n")
        findings = scan_file(f)
        assert any(fi.rule_id == "CPY011" for fi in findings)

    def test_pypy_only_branch_suppresses_cpython_finding(self, tmp_path):
        f = tmp_path / "pypy_branch.py"
        f.write_text(
            textwrap.dedent(
                """
                import sys
                if sys.implementation.name == "pypy":
                    from typing import Self
                """
            )
        )
        findings = scan_file(f)
        assert not any(fi.rule_id == "CPY011" for fi in findings)


class TestNestedAndElifIntervalComposition:
    """Item #4 (2026-09 audit): nested/elif version guards must compose
    via interval intersection, not just consider the innermost `if` in
    isolation."""

    def test_nested_if_composes_bounded_interval(self):
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 12):
                    if sys.version_info < (3, 15):
                        from collections.abc import ByteString
                """
            )
        )
        # composed reachable range for the innermost body is [3.12, 3.15)
        should_suppress, _reason = guard_reduces_risk(
            index,
            5,
            finding_runtime="cpython",
            affected_from="3.15",
            affected_until="",
            category="compatibility",
        )
        assert should_suppress

    def test_nested_if_does_not_falsely_suppress_overlapping_finding(self):
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 12):
                    if sys.version_info < (3, 17):
                        from collections.abc import ByteString
                """
            )
        )
        # composed reachable range [3.12, 3.17) genuinely overlaps a
        # [3.15, 3.17) affected window -- must NOT suppress.
        should_suppress, _reason = guard_reduces_risk(
            index,
            5,
            finding_runtime="cpython",
            affected_from="3.15",
            affected_until="3.17",
            category="compatibility",
        )
        assert not should_suppress

    def test_elif_chain_composes_bounded_interval(self):
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 14):
                    pass
                elif sys.version_info >= (3, 12):
                    from collections.abc import ByteString
                else:
                    pass
                """
            )
        )
        # elif body's composed reachable range is [3.12, 3.14) --
        # disjoint from a [3.15, inf) affected finding.
        should_suppress, _reason = guard_reduces_risk(
            index,
            6,
            finding_runtime="cpython",
            affected_from="3.15",
            affected_until="",
            category="compatibility",
        )
        assert should_suppress

    def test_elif_else_branch_composes_correctly(self):
        index = build_guard_index(
            parse(
                """
                import sys
                if sys.version_info >= (3, 14):
                    pass
                elif sys.version_info >= (3, 12):
                    pass
                else:
                    from collections.abc import ByteString
                """
            )
        )
        # else body's composed reachable range is (-inf, 3.12) --
        # disjoint from a [3.15, inf) affected finding.
        should_suppress, _reason = guard_reduces_risk(
            index,
            8,
            finding_runtime="cpython",
            affected_from="3.15",
            affected_until="",
            category="compatibility",
        )
        assert should_suppress

    def test_nested_guard_inside_function_still_composes(self):
        """A version guard inside a function body still needs the
        surrounding module-level guard context, if any (here there's no
        outer guard, but the nested `if` inside the function must still
        get its own composed context correctly, exercising the
        recursion into non-`if` statement containers)."""
        index = build_guard_index(
            parse(
                """
                import sys

                def setup():
                    if sys.version_info >= (3, 12):
                        if sys.version_info < (3, 15):
                            from collections.abc import ByteString
                """
            )
        )
        should_suppress, _reason = guard_reduces_risk(
            index,
            7,
            finding_runtime="cpython",
            affected_from="3.15",
            affected_until="",
            category="compatibility",
        )
        assert should_suppress
