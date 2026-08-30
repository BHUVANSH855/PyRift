"""
PPY018 — sys.setrecursionlimit behaves differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sys.setrecursionlimit(n) sets the maximum recursion
depth to exactly n. On PyPy, it sets the usable stack space to
n * 768 bytes — the actual recursion depth depends on the stack
frame size, not a direct count. The default of 768KB supports
about 1400 calls on Linux.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class RecursionLimitRule(BaseRule):
    rule_id = "PPY018"
    title   = "sys.setrecursionlimit() behaviour differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "setrecursionlimit" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "sys"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "sys.setrecursionlimit(n) on CPython sets the exact "
                        "maximum recursion depth to n. On PyPy, it sets "
                        "the usable stack space to n * 768 bytes — the actual "
                        "number of recursive calls allowed depends on frame size "
                        "and is approximately n/5 on most platforms. Code that "
                        "sets a specific recursion limit may behave differently "
                        "on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "If you need deep recursion on PyPy, set the limit "
                        "significantly higher than on CPython, or convert "
                        "the recursion to an explicit stack-based iteration."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#miscellaneous"
                    ),
                ))
        return findings