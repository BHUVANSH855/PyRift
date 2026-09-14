"""
CPY023 — multiprocessing fork start method changing in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The default multiprocessing start method on POSIX platforms (excluding
macOS, which has defaulted to 'spawn' since Python 3.8) changes from
'fork' to 'forkserver' in Python 3.14. Code relying on the default
'fork' behaviour may silently break.

Narrowed 2026-09-13 (review, point 7): a bare ``import multiprocessing``
is not evidence that a program relies on fork semantics -- plenty of
code imports the module and only ever uses ``Pool``/``Process`` in ways
that don't care about the start method. The rule now requires actual
use of a start-method-sensitive construct (``Process(...)``,
``Pool(...)``, or ``get_context()`` without an explicit method) before
firing, and is downgraded to MEDIUM confidence accordingly (see
``pyrift.rule_metadata``) since even that is still a proxy for "may be
fork-sensitive", not proof of it. Also excludes macOS, whose default was
never 'fork' to begin with, per the official multiprocessing docs.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

if TYPE_CHECKING:
    from pyrift.targets import TargetConfig

_EXCLUDED_PLATFORMS = {"windows", "win32", "macos", "darwin", "osx"}

# Constructs whose behavior can plausibly depend on the process start
# method. A bare `import multiprocessing` alone no longer triggers this
# rule -- see module docstring.
_START_METHOD_SENSITIVE_ATTRS = {"Process", "Pool", "get_context"}


def _has_explicit_start_method(node: ast.AST) -> bool:
    """Return True if the file already calls set_start_method or get_context
    with an explicit method argument."""
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        func = n.func
        if isinstance(func, ast.Attribute) and func.attr == "set_start_method":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "get_context" and n.args:
            # get_context("fork") / get_context("spawn") / etc. is already
            # explicit and version-safe.
            return True
    return False


def _uses_start_method_sensitive_api(node: ast.AST) -> ast.Call | None:
    """Return the first AST call that plausibly depends on the default
    start method (Process/Pool construction, or a bare get_context()),
    or None if no such usage is found."""
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        func = n.func
        if isinstance(func, ast.Attribute) and func.attr in _START_METHOD_SENSITIVE_ATTRS:
            if func.attr == "get_context" and n.args:
                continue  # explicit method argument -- not a risk
            return n
    return None


class MultiprocessingForkRule(BaseRule):
    rule_id = "CPY023"
    title = "multiprocessing default start method changing in Python 3.14"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        if (
            target_config is not None
            and target_config.platform is not None
            and target_config.platform.lower() in _EXCLUDED_PLATFORMS
        ):
            return []

        # If the file already sets the start method explicitly — no finding
        if _has_explicit_start_method(node):
            return []

        has_multiprocessing_import = any(
            isinstance(n, ast.Import) and any(a.name == "multiprocessing" for a in n.names)
            for n in ast.walk(node)
        )
        if not has_multiprocessing_import:
            return []

        risky_call = _uses_start_method_sensitive_api(node)
        if risky_call is None:
            # multiprocessing is imported but never used in a way that
            # plausibly depends on the start method -- nothing to report.
            return []

        return [Finding(
            file=filename,
            line=risky_call.lineno,
            col=risky_call.col_offset,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "The default multiprocessing start method on "
                "Linux/BSD/POSIX (excluding macOS) is 'fork' in Python "
                "<= 3.13. In Python 3.14 it changes to 'forkserver'. "
                "This file constructs a Process/Pool or calls "
                "get_context() without pinning a start method; if it "
                "relies on fork semantics (shared memory, inherited "
                "file descriptors, or process creation outside an "
                "`if __name__ == '__main__':` guard) it may silently "
                "break."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Explicitly set the start method: "
                "multiprocessing.set_start_method('fork') "
                "or use multiprocessing.get_context('fork') "
                "to make the behaviour explicit and version-safe."
            ),
            docs_url=(
                "https://docs.python.org/3/library/multiprocessing.html"
                "#contexts-and-start-methods"
            ),
        )]