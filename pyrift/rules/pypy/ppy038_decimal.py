"""
PPY038 — Decimal module uses different backend on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, the decimal module uses a fast C implementation
(_decimal). On PyPy, decimal is implemented in pure Python
(or RPython), which means performance differs significantly
and some edge cases in rounding and context handling may
produce different results.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class DecimalBackendRule(BaseRule):
    rule_id = "PPY038"
    title   = "decimal module uses different backend on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "decimal":
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom) and n.module == "decimal":
                mod = n.module
                line, col = n.lineno, n.col_offset
            if mod:
                findings.append(Finding(
                    file=filename,
                    line=line,
                    col=col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The decimal module is imported. On CPython, decimal "
                        "uses a fast C implementation. On PyPy, it uses a "
                        "pure Python/RPython implementation which is slower "
                        "and may have subtle differences in rounding behaviour "
                        "and context handling in edge cases."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Test decimal-heavy code on PyPy explicitly. "
                        "For high-precision financial calculations, verify "
                        "rounding behaviour matches expectations on both "
                        "CPython and PyPy with your specific data."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))
        return findings