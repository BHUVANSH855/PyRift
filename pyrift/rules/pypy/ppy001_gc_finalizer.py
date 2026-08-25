"""
PPY001 — Relying on __del__ for resource cleanup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CPython uses reference counting — __del__ is called immediately.
PyPy uses a tracing GC — __del__ may never be called or called
much later. Code relying on __del__ silently leaks on PyPy.
"""
from __future__ import annotations

import ast
from typing import ClassVar

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class GcFinalizerRule(BaseRule):
    rule_id = "PPY001"
    title   = "Relying on __del__ for resource cleanup breaks on PyPy"
    runtime = "pypy"

    RESOURCE_PATTERNS: ClassVar[set[str]] = {
        "close",
        "flush",
        "release",
        "disconnect",
        "cleanup",
        "shutdown",
        "terminate",
    }

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.FunctionDef):
                continue
            if n.name != "__del__":
                continue

            for child in ast.walk(n):
                if isinstance(child, ast.Call):
                    func = child.func
                    method = None
                    if isinstance(func, ast.Attribute):
                        method = func.attr
                    elif isinstance(func, ast.Name):
                        method = func.id
                    if method and method in self.RESOURCE_PATTERNS:
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                f"__del__ calls '{method}()' for resource cleanup. "
                                "On CPython, __del__ is called immediately when the "
                                "object goes out of scope (reference counting). "
                                "On PyPy, the GC is non-reference-counting — "
                                "__del__ may be called much later or not at all, "
                                "silently leaking file handles, sockets, or locks."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.PYPY,
                            affected_from="any",
                            suggestion=(
                                "Use context managers (with statement) or "
                                "try/finally blocks for guaranteed cleanup. "
                                "Never rely on __del__ for correctness."
                            ),
                            docs_url=(
                                "https://doc.pypy.org/en/latest/cpython_differences.html"
                                "#differences-related-to-garbage-collection-strategies"
                            ),
                        ))
                        break

        return findings