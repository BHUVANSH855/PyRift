"""
CPY042 — aiter() and anext() builtins require Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The builtin functions aiter() and anext() were added in Python 3.10
as async counterparts to iter() and next(). Using them on 3.9 or
below raises NameError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

ASYNC_BUILTINS = {"aiter", "anext"}


class AiterAnextRule(BaseRule):
    rule_id = "CPY042"
    title   = "aiter() and anext() builtins require Python 3.10+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if isinstance(func, ast.Name) and func.id in ASYNC_BUILTINS:
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"{func.id}() was added as a builtin in Python 3.10. "
                        "Calling it on Python 3.9 or below raises NameError "
                        "at runtime — it does not exist as a builtin."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.9",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 10): "
                        f"use {func.id}() "
                        "or implement the async iteration manually for 3.9."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/functions.html"
                        f"#{func.id}"
                    ),
                ))
        return findings