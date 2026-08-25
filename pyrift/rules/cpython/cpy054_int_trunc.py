"""
CPY054 — int() no longer delegates to __trunc__ in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before Python 3.14, int() would call __trunc__() on objects that
did not implement __int__() or __index__(). In Python 3.14, this
delegation was removed. Custom numeric types relying on __trunc__()
for int() conversion silently break — int(obj) raises TypeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class IntTruncRule(BaseRule):
    rule_id = "CPY054"
    title   = "int() no longer delegates to __trunc__() in Python 3.14"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.FunctionDef):
                continue
            if n.name != "__trunc__":
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "__trunc__() method is defined here. Before Python 3.14, "
                    "int() would call __trunc__() on objects that did not "
                    "implement __int__() or __index__(). In Python 3.14, "
                    "this delegation was removed — int(obj) now raises "
                    "TypeError if __int__() and __index__() are missing, "
                    "even if __trunc__() is defined. Custom numeric types "
                    "relying on __trunc__() for int() conversion silently "
                    "break on Python 3.14+."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.14",
                suggestion=(
                    "Implement __int__() or __index__() instead of __trunc__(). "
                    "def __int__(self): return int(self._value) "
                    "__trunc__() is still called by math.trunc() but no "
                    "longer by int()."
                ),
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.14.html"
                    "#changes-in-the-python-api"
                ),
            ))
        return findings