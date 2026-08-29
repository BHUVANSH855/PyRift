"""
CPY034 — int.bit_count() requires Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
int.bit_count() was added in Python 3.10.
Calling it on Python 3.9 or below raises AttributeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class BitCountRule(BaseRule):
    rule_id = "CPY034"
    title   = "int.bit_count() requires Python 3.10+"
    runtime = "cpython"

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
                    func.attr == "bit_count"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "int.bit_count() was added in Python 3.10. "
                        "Calling it on Python 3.9 or below raises "
                        "AttributeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.9",
                    suggestion=(
                        "For Python 3.9 compatibility use: "
                        "bin(n).count('1') "
                        "which works on all Python 3 versions."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/stdtypes.html"
                        "#int.bit_count"
                    ),
                ))
        return findings