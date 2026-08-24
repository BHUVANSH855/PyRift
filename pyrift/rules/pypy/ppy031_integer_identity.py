"""
PPY031 — Integer identity (is) always True on PyPy for all ints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, only small integers (-5 to 256) are cached — for larger
integers, x is y may be False even if x == y. On PyPy, ALL integers
are unique by value — x + 1 is x + 1 is always True for any integer.
Code that relies on integer identity being False for large integers
will silently behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class IntegerIdentityRule(BaseRule):
    rule_id = "PPY031"
    title   = "Integer 'is' identity semantics differ on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Compare):
                continue
            # Detect: x is y or x is not y where operands look like integers
            for op in n.ops:
                if isinstance(op, (ast.Is, ast.IsNot)):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "'is' or 'is not' comparison detected. "
                            "On CPython, only small integers (-5 to 256) "
                            "are cached — 'x is y' may be False for larger "
                            "integers even when x == y. "
                            "On PyPy, ALL integers are unique by value — "
                            "'x + 1 is x + 1' is always True for any integer. "
                            "If comparing integers, this will silently differ "
                            "between runtimes."
                        ),
                        severity=Severity.INFO,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Use '==' instead of 'is' for value equality. "
                            "Reserve 'is' only for None, True, False, "
                            "and sentinel object identity checks."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                            "#object-identity-of-primitive-values-is-and-id"
                        ),
                    ))
                    break  # one finding per Compare node
        return findings