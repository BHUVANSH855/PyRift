"""
PPY007 — sys.intern() behaviour differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sys.intern() interns a string so all equal interned
strings share the same object identity (is comparison). On PyPy,
string interning exists but identity guarantees are weaker due to
the JIT — code relying on interned string identity may silently
produce wrong results.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class SysInternRule(BaseRule):
    rule_id = "PPY007"
    title   = "sys.intern() identity guarantees differ on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "sys" and
                    func.attr == "intern"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "sys.intern() is used here. On CPython, interned "
                        "strings are guaranteed to share identity — "
                        "'a' is 'b' returns True for equal interned strings. "
                        "On PyPy, the JIT may or may not preserve this "
                        "identity guarantee, making 'is' comparisons on "
                        "interned strings unreliable across runtimes."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use == for string equality instead of 'is'. "
                        "Never rely on string identity for correctness — "
                        "it is an implementation detail of CPython."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))

        return findings