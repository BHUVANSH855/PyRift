"""
PPY003 — sys.getrefcount() is meaningless on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CPython uses reference counting — sys.getrefcount() returns a real
meaningful value. PyPy uses a tracing GC with no reference counting —
sys.getrefcount() always returns a dummy value (typically 0 or 65536).
Code that makes decisions based on sys.getrefcount() breaks silently.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class GetRefcountRule(BaseRule):
    rule_id = "PPY003"
    title   = "sys.getrefcount() is meaningless on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "sys"
                and func.attr == "getrefcount"
            ):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "sys.getrefcount() relies on CPython's reference "
                            "counting GC. PyPy uses a tracing GC with no reference "
                            "counting — sys.getrefcount() always returns a dummy "
                            "value on PyPy. Any logic based on this value will "
                            "silently produce wrong results on PyPy."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Do not use sys.getrefcount() for correctness logic. "
                            "If debugging memory, use gc.get_referrers() instead "
                            "which works on both runtimes."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                        ),
                    ))

        return findings