"""
PPY019 — float('nan') identity differs between CPython and PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, float('nan') is float('nan') is False — each call
creates a new object. On PyPy, there is only one object per bit
pattern — float('nan') is float('nan') is True. This means sets
cannot contain multiple NaN values on PyPy, but can on CPython.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class NanIdentityRule(BaseRule):
    rule_id = "PPY019"
    title   = "float('nan') identity differs between CPython and PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Detect float('nan') calls
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (isinstance(func, ast.Name) and func.id == "float"):
                continue
            if not n.args:
                continue
            arg = n.args[0]
            if (isinstance(arg, ast.Constant) and
                    isinstance(arg.value, str) and
                    arg.value.lower() in ("nan", "+nan", "-nan")):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "float('nan') creates a new object each time on "
                        "CPython — so float('nan') is float('nan') is False "
                        "and a set can contain multiple NaN values. "
                        "On PyPy, there is only one NaN object per bit pattern "
                        "— float('nan') is float('nan') is True, and a set "
                        "cannot contain multiple NaN values. This causes "
                        "silent behaviour differences in set operations."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use math.isnan() to check for NaN rather than "
                        "identity comparisons. Do not rely on multiple NaN "
                        "values in a set — use filtering instead."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#object-identity-of-primitive-values-is-and-id"
                    ),
                ))

        return findings