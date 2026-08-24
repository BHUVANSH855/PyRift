"""
PPY034 — hash(-1) returns -2 on CPython, may differ on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, hash(-1) returns -2 because -1 is reserved as an
error indicator in CPython's C implementation. PyPy tries to
match this behaviour but there are edge cases where hash values
for certain objects differ between runtimes, silently causing
dict/set lookups to fail or produce wrong results.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class HashMinusOneRule(BaseRule):
    rule_id = "PPY034"
    title   = "hash() values may differ between CPython and PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (isinstance(func, ast.Name) and func.id == "hash"):
                continue
            # Flag when hash result is compared or stored
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "hash() is called here. On CPython, hash(-1) returns -2 "
                    "because -1 is reserved as an error indicator in C. "
                    "PyPy matches this for integers, but hash values for "
                    "certain custom objects or edge cases may differ between "
                    "runtimes. Code that stores or compares hash values "
                    "across sessions or runtimes may silently fail."
                ),
                severity=Severity.INFO,
                runtime=Runtime.PYPY,
                suggestion=(
                    "Never store hash values persistently or compare them "
                    "across different Python runtimes. Hash values are "
                    "implementation-specific and not guaranteed to be "
                    "consistent between CPython and PyPy."
                ),
                docs_url=(
                    "https://doc.pypy.org/en/latest/cpython_differences.html"
                    "#miscellaneous"
                ),
            ))
        return findings