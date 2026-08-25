"""
CPY023 — multiprocessing fork start method changing in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The default multiprocessing start method on POSIX platforms changes
from 'fork' to a safer method in Python 3.14. Code relying on the
default 'fork' behaviour may silently break.

Only flag when the file does not already call set_start_method() or
get_context() — those calls make the start method explicit and safe.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

if TYPE_CHECKING:
    from pyrift.targets import TargetConfig


def _has_explicit_start_method(node: ast.AST) -> bool:
    """Return True if the file already calls set_start_method or get_context."""
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        func = n.func
        if isinstance(func, ast.Attribute) and func.attr in (
            "set_start_method",
            "get_context",
        ):
            return True
    return False


class MultiprocessingForkRule(BaseRule):
    rule_id = "CPY023"
    title = "multiprocessing default start method changing in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        if (
            target_config is not None
            and target_config.platform is not None
            and target_config.platform.lower() in {"windows", "win32"}
        ):
            return []

        # If the file already sets the start method explicitly — no finding
        if _has_explicit_start_method(node):
            return []

        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Import):
                continue
            for alias in n.names:
                if alias.name != "multiprocessing":
                    continue
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The default multiprocessing start method on "
                        "Linux/BSD/POSIX is 'fork' in Python <= 3.13. "
                        "In Python 3.14 it changed to 'forkserver'. "
                        "Code relying on fork semantics (shared memory, "
                        "inherited file descriptors) may silently break."
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
                ))

        return findings