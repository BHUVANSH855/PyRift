"""
PPY013 — sys.getsizeof() raises TypeError on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sys.getsizeof() returns the memory size of an object.
On PyPy, sys.getsizeof() always raises TypeError because memory
profiling based on this function gives results inconsistent with
reality on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class GetSizeofRule(BaseRule):
    rule_id = "PPY013"
    title   = "sys.getsizeof() raises TypeError on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "getsizeof" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "sys"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "sys.getsizeof() always raises TypeError on PyPy. "
                        "PyPy deliberately does not implement it because "
                        "memory profiling based on object sizes gives results "
                        "inconsistent with reality on PyPy's GC. "
                        "Code using sys.getsizeof() will crash on PyPy."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use a PyPy-compatible memory profiler like vmprof "
                        "instead of sys.getsizeof(). "
                        "If you need object size estimation, guard with: "
                        "if hasattr(sys, '__pypy__'): ... else: sys.getsizeof(x)"
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#miscellaneous"
                    ),
                ))
        return findings