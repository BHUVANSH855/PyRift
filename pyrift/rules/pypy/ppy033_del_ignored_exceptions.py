"""
PPY033 — Exceptions in __del__ are ignored differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, if __del__ raises an exception, a warning is printed
to stderr and the exception is ignored. On PyPy, exceptions in
__del__ are also ignored but the warning may appear at a very
different time — sometimes long after the object was collected,
making debugging extremely difficult.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class DelIgnoredExceptionsRule(BaseRule):
    rule_id = "PPY033"
    title   = "Exceptions in __del__ appear at unpredictable times on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.FunctionDef):
                continue
            if n.name != "__del__":
                continue
            # Check if __del__ has any raise or function calls that might raise
            has_risky_code = any(
                isinstance(child, (ast.Raise, ast.Call))
                for child in ast.walk(n)
            )
            if has_risky_code:
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "__del__ contains code that may raise exceptions. "
                        "On CPython, exceptions in __del__ produce a warning "
                        "to stderr immediately when the object is collected. "
                        "On PyPy, the warning appears at an unpredictable "
                        "time — possibly long after the object was collected — "
                        "making debugging very difficult."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Wrap all __del__ body in try/except to prevent "
                        "exceptions from escaping: "
                        "try: self.cleanup() except Exception: pass. "
                        "Better: use context managers instead of __del__."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                ))
        return findings