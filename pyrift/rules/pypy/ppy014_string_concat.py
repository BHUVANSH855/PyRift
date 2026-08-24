"""
PPY014 — Repeated string concatenation in loops is O(n²) on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CPython has an optimisation that makes repeated string concatenation
in simple loops run in O(n) time. PyPy does not have this optimisation
— string concatenation in loops is always O(n²) on PyPy, silently
degrading performance on large inputs.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class StringConcatLoopRule(BaseRule):
    rule_id = "PPY014"
    title   = "String concatenation in loop is O(n²) on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, (ast.For, ast.While)):
                continue
            # Look for augmented assignment s += something in loop body
            for child in ast.walk(n):
                if isinstance(child, ast.AugAssign):
                    if isinstance(child.op, ast.Add):
                        # Check if target is a simple name (string variable)
                        if isinstance(child.target, ast.Name):
                            findings.append(Finding(
                                file=filename,
                                line=child.lineno,
                                col=child.col_offset,
                                rule_id=self.rule_id,
                                title=self.title,
                                description=(
                                    f"'{child.target.id} +=' inside a loop may "
                                    "be string concatenation. CPython has a "
                                    "special optimisation making this O(n). "
                                    "PyPy does not — this is always O(n²) on "
                                    "PyPy, silently causing severe performance "
                                    "degradation on large inputs."
                                ),
                                severity=Severity.WARNING,
                                runtime=Runtime.PYPY,
                                suggestion=(
                                    "Use a list and join at the end: "
                                    "parts = []; parts.append(s); result = ''.join(parts). "
                                    "This is O(n) on both CPython and PyPy."
                                ),
                                docs_url=(
                                    "https://doc.pypy.org/en/latest/"
                                    "cpython_differences.html#performance-differences"
                                ),
                            ))
                            break

        return findings