"""
CPY050 — PurePath.is_reserved() deprecated in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pathlib.PurePath.is_reserved() was deprecated in Python 3.13
and will be removed in Python 3.15. On Windows, use
os.path.isreserved() instead. On other platforms, the method
always returned False anyway.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class PurePathIsReservedRule(BaseRule):
    rule_id = "CPY050"
    title   = "PurePath.is_reserved() deprecated in 3.13, removed in 3.15"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "is_reserved"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "pathlib.PurePath.is_reserved() was deprecated in "
                        "Python 3.13 and will be removed in Python 3.15. "
                        "On non-Windows platforms it always returned False. "
                        "On Windows, use os.path.isreserved() instead."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "Replace with: import os; os.path.isreserved(path) "
                        "for Windows reserved path detection. "
                        "This works on Python 3.13+ on all platforms."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/pathlib.html"
                    ),
                ))
        return findings