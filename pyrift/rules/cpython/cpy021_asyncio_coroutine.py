"""
CPY021 — asyncio.iscoroutinefunction() deprecated, use inspect version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
asyncio.iscoroutinefunction() was deprecated in Python 3.12 and will
be removed in Python 3.16. Use inspect.iscoroutinefunction() instead.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class AsyncioIsCoroutineRule(BaseRule):
    rule_id = "CPY021"
    title   = "asyncio.iscoroutinefunction() deprecated since 3.12"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "iscoroutinefunction" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "asyncio"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "asyncio.iscoroutinefunction() was deprecated in "
                        "Python 3.12 and will be removed in Python 3.16. "
                        "Using it after removal raises AttributeError."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Replace with inspect.iscoroutinefunction(func) "
                        "which works on all Python 3 versions."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/asyncio-task.html"
                    ),
                ))
        return findings