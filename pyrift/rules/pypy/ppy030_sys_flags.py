"""
PPY030 — sys.flags.ignore_environment differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Several sys.flags values behave differently on PyPy compared to
CPython. Most notably, sys.flags related to hash randomisation
and environment handling have different defaults or meanings on
PyPy due to PyPy's different startup behaviour.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

PYPY_DIFFERENT_FLAGS = {
    "hash_randomization",
    "ignore_environment",
    "isolated",
}


class SysFlagsRule(BaseRule):
    rule_id = "PPY030"
    title   = "sys.flags values may differ between CPython and PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Attribute):
                continue
            if n.attr not in PYPY_DIFFERENT_FLAGS:
                continue
            if not (isinstance(n.value, ast.Attribute) and
                    n.value.attr == "flags" and
                    isinstance(n.value.value, ast.Name) and
                    n.value.value.id == "sys"):
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"sys.flags.{n.attr} is accessed here. This flag "
                    "may have different values or semantics on PyPy "
                    "compared to CPython. In particular, "
                    "hash_randomization is always 1 on PyPy regardless "
                    "of PYTHONHASHSEED, and other flags may reflect "
                    "PyPy-specific startup behaviour."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.PYPY,
                suggestion=(
                    "Do not rely on sys.flags values being identical "
                    "between CPython and PyPy. Test explicitly on PyPy "
                    "if your code behaviour depends on these flags."
                ),
                docs_url=(
                    "https://doc.pypy.org/en/latest/cpython_differences.html"
                    "#miscellaneous"
                ),
            ))
        return findings