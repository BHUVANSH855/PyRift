"""
PPY044 — Exception __traceback__ cleanup differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, when an exception is stored in a variable and the
except block exits, CPython explicitly deletes the variable to
break reference cycles (PEP 3110). On PyPy, this cleanup
happens at a different time due to GC differences, meaning
the exception object and its traceback may stay alive longer,
holding references to local variables in the frame.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class ExceptionChainingRule(BaseRule):
    rule_id = "PPY044"
    title   = "Exception variable cleanup timing differs on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.ExceptHandler):
                continue
            if n.name is None:
                continue
            # except SomeError as e — the 'e' variable
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"Exception is caught as '{n.name}'. On CPython, "
                    "the exception variable is explicitly deleted when "
                    "the except block exits (PEP 3110) to break reference "
                    "cycles. On PyPy, this deletion happens at a different "
                    "time due to GC timing — the exception and its traceback "
                    "may hold references to frame locals longer, causing "
                    "unexpected memory retention."
                ),
                severity=Severity.INFO,
                runtime=Runtime.PYPY,
                suggestion=(
                    f"If you need '{n.name}' after the except block, "
                    f"assign it to another variable first: "
                    f"saved_exc = {n.name}. "
                    "This works consistently on both CPython and PyPy."
                ),
                docs_url=(
                    "https://doc.pypy.org/en/latest/cpython_differences.html"
                    "#differences-related-to-garbage-collection-strategies"
                ),
            ))
        return findings