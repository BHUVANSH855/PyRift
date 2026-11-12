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
from pyrift.targets import TargetConfig


class UnionTypeSyntaxRule(BaseRule):
    rule_id = "CPY003"
    title   = "X | Y union type syntax requires Python 3.10+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        # Single O(n) pass: collect node IDs used as 2nd arg of isinstance/issubclass.
        isinstance_args: set[int] = set()
        for n in ast.walk(node):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in ("isinstance", "issubclass")
                and len(n.args) >= 2
            ):
                isinstance_args.add(id(n.args[1]))

        # Single O(n) pass: flag X | Y BinOp nodes that appear as the 2nd arg.
        findings: list[Finding] = []
        for n in ast.walk(node):
            if (
                isinstance(n, ast.BinOp)
                and isinstance(n.op, ast.BitOr)
                and id(n) in isinstance_args
            ):
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