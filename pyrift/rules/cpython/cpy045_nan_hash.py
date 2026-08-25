"""
CPY045 — NaN hash behaviour changed in Python 3.10
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before Python 3.10, hash(float('nan')) always returned 0, causing
quadratic runtime when creating dicts/sets with multiple NaN values.
In Python 3.10, NaN hashes depend on object identity. Code relying
on NaN hashing to 0 will silently break on 3.10+.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class NanHashRule(BaseRule):
    rule_id = "CPY045"
    title   = "NaN hash behaviour changed in Python 3.10"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (isinstance(func, ast.Name) and func.id == "hash"):
                continue
            if not n.args:
                continue
            arg = n.args[0]
            # Detect hash(float('nan'))
            if isinstance(arg, ast.Call):
                inner = arg.func
                if (
                    isinstance(inner, ast.Name)
                    and inner.id == "float"
                    and arg.args
                    and isinstance(arg.args[0], ast.Constant)
                    and str(arg.args[0].value).lower() in ("nan", "+nan", "-nan")
                ):
                    findings.append(Finding(
                                file=filename,
                                line=n.lineno,
                                col=n.col_offset,
                                rule_id=self.rule_id,
                                title=self.title,
                                description=(
                                    "hash(float('nan')) always returned 0 "
                                    "before Python 3.10, causing quadratic "
                                    "runtime with multiple NaN values in dicts "
                                    "and sets. In Python 3.10+, NaN hashes "
                                    "depend on object identity. Code relying "
                                    "on hash(nan) == 0 will silently break."
                                ),
                                severity=Severity.WARNING,
                                runtime=Runtime.CPYTHON,
                                affected_from="3.10",
                                suggestion=(
                                    "Never rely on the specific hash value of NaN. "
                                    "Use math.isnan() to check for NaN, and "
                                    "avoid using NaN as dict keys or set members."
                                ),
                                docs_url=(
                                    "https://docs.python.org/3/whatsnew/3.10.html"
                                ),
                            ))
        return findings