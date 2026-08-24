"""
CPY003 — Union type syntax X | Y requires Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PEP 604 introduced int | str as a replacement for Union[int, str].
Using it at runtime inside isinstance() raises TypeError on 3.9-.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class UnionTypeSyntaxRule(BaseRule):
    rule_id = "CPY003"
    title   = "X | Y union type syntax requires Python 3.10+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.BinOp):
                continue
            if not isinstance(n.op, ast.BitOr):
                continue
            if self._in_isinstance(n, node):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "Using X | Y as a runtime type expression inside "
                        "isinstance() or issubclass() requires Python 3.10+. "
                        "On 3.9 and below this raises TypeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.9",
                    suggestion=(
                        "Use a tuple instead: isinstance(x, (int, str)) "
                        "which works on all Python 3 versions."
                    ),
                    docs_url="https://peps.python.org/pep-0604/",
                ))

        return findings

    @staticmethod
    def _in_isinstance(target: ast.AST, tree: ast.AST) -> bool:
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                func = n.func
                if isinstance(func, ast.Name) and func.id in ("isinstance", "issubclass"):
                    if len(n.args) >= 2 and n.args[1] is target:
                        return True
        return False